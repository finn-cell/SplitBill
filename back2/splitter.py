import pandas as pd
import warnings
warnings.filterwarnings("ignore")

### TODO:
### 葷素系統
### UI
### 日期
### 分帳比例

class ExpenseSplitter:
    def __init__(self, participants, digit=0):
        """
        初始化分帳程式，設置參與者列表
        :param participants: 參與者列表 (list of str)
        """
        self.digit = digit
        self.participants = participants
        # 初始化支出記錄，包含每位參與者的支出紀錄欄位
        columns = ['payer', 'amount', 'item', 'participants'] + participants + ['receive_from_' + name for name in participants]
        self.expensesDf = pd.DataFrame(columns=columns)
    
    def add_participant(self, name):
        """
        新增參與者，並更新支出記錄的欄位
        :param participant: 新的參與者名稱 (str)
        """
        if name not in self.participants:
            self.participants.append(name)
            self.expensesDf[name] = 0
            self.expensesDf['receive_from_' + name] = 0

    def delete_participant(self, participant):
        """
        刪除參與者，並更新支出記錄的欄位
        :param participant: 要刪除的參與者名稱 (str)
        """
        if participant in self.participants:
            self.participants.remove(participant)
            self.expensesDf = self.expensesDf.drop(columns=[participant, 'receive_from_' + participant])

    def get_participant(self):
        print(f"All participants {self.participants}")
        return self.participants
    
    def refresh_expenses(self):
        """
        清空所有支出記錄
        """
        columns = ['payer', 'amount', 'item'] + self.participants + ['receive_from_' + name for name in self.participants]
        self.expensesDf = pd.DataFrame(columns=columns)

    def add_expense(self, payer, amount, item, participants):
        """
        新增一筆支出記錄，並標註參與者
        :param payer: 支付者 (str)
        :param amount: 金額 (float)
        :param item: 消費項目 (str)
        :param participants: 參與者列表 (list of str)
        """
        peopleCont = 0
        expenseData = {'payer': [payer], 'amount': [amount], 'item': [item]}
        
        ### record who will join to split this bill
        for participant in self.participants:
            if participant in participants:
                expenseData[participant] = [1]
                peopleCont += 1
            else:
                expenseData[participant] = [0]
        
        if self.digit == 0:
            if expenseData['amount'][0] % peopleCont >= 5:
                money = int(expenseData['amount'][0] / peopleCont) + 1
            else:
                money = int(expenseData['amount'][0] / peopleCont)
        else:
            money = round(expenseData['amount'][0] / peopleCont, self.digit)

        ### setting the participant and money relation
        for participant in self.participants:
            if participant in participants:
                expenseData['receive_from_' + participant] = [money]
                peopleCont += 1
            else:
                expenseData['receive_from_' + participant] = [0]

        ### add this bill to DF
        self.expensesDf = pd.concat([self.expensesDf, pd.DataFrame(expenseData)], ignore_index=True)

        # 定義排除欄位
        exclude_prefixes = ["receive_from_"]
        exclude_exact = ["payer", "amount", "item"]

        # 判斷是參與者的欄位
        participant_columns = [
            col for col in self.expensesDf.columns
            if not any(col.startswith(prefix) for prefix in exclude_prefixes)
            and col not in exclude_exact
        ]

        # 建立 participants 欄位
        self.expensesDf["participants"] = self.expensesDf[participant_columns].apply(
            lambda row: [col for col in participant_columns if row[col] == 1],
            axis=1
        )

    def delete_expense(self, index):
        """
        根據索引刪除指定支出記錄
        :param index: 欲刪除的支出記錄索引 (int)
        """
        if 0 <= index < len(self.expensesDf):
            self.expensesDf = self.expensesDf.drop(index=index).reset_index(drop=True)

    def __aggregate_items(self, group):
        itemsSummary = {}
        for _, row in group.iterrows():
            item = row["item"]
            amount = row["amount"]
            if item in itemsSummary:
                itemsSummary[item] += amount
            else:
                itemsSummary[item] = amount
        
        ### format to "{Item}: {Amount}, "
        if self.digit == 0:
            return ", ".join(f"{item}: {amount}" for item, amount in itemsSummary.items())
        else:
            return ", ".join(f"{item}: {amount:.{self.digit}f}" for item, amount in itemsSummary.items())
                    
    def make_bill_relation(self):
        """
        計算每位參與者的結餘
        :return: 每位參與者的結餘 (DataFrame)
        """
        ### 把錢 summary -> 誰 pay 誰 多少錢，有什麼 Item
        transactions = []
        for _, row in self.expensesDf.iterrows():
            payer = row["payer"]; item = row["item"]
            for person in self.participants:
                if payer != person:
                    amountToPay = row[f"receive_from_{person}"]
                    transactions.append({"from": person, "to": payer, "amount": amountToPay, "item": item})
        
        resultDf = pd.DataFrame(transactions)
        resultDf = resultDf[resultDf["amount"] > 0]
        return resultDf
    
    def cal_all_item_bill(self, resultDf):
        ### 把 Item 的錢列出來，方便驗算
        balanceDf = (
            resultDf.groupby(["from", "to"])
                .apply(lambda group: pd.Series({
                "total_amount": group["amount"].sum(),
                "detailed_items": self.__aggregate_items(group),
            })).reset_index()
        )    

        return balanceDf
    
    def cal_simplified_balances(self, resultDf):
        ### 建 receiver & payer Dict
        balancesDict = {}
        for _, row in resultDf.iterrows():
            key = (row["from"], row["to"])
            if key not in balancesDict:
                balancesDict[key] = 0
            balancesDict[key] += row["amount"]

        ### 消除雙向付款
        ### EX: A -> B: 90$, B -> A: 40$ --> final: A -> B: 50$
        simplifiedBalancesList = []
        for (payer, receiver), amount in balancesDict.items():
            reverseKey = (receiver, payer)
            if reverseKey in balancesDict:
                if balancesDict[reverseKey] > amount:
                    balancesDict[reverseKey] -= amount
                    amount = 0
                else:
                    amount -= balancesDict[reverseKey]
                    balancesDict[reverseKey] = 0
            if amount > 0:
                simplifiedBalancesList.append({"from": payer, "to": receiver, "amount": amount})

        simplifiedBalancesDf = pd.DataFrame(simplifiedBalancesList)
        simplifiedBalancesDf = simplifiedBalancesDf.sort_values(by="from").reset_index(drop=True)
        return simplifiedBalancesDf      

    def cal_receive_pay_summary(self, balanceDf):
        ### cal everyone total pay
        payerSummary = balanceDf.groupby("from")["total_amount"].sum().reset_index()
        payerSummary["type"] = "pay"
        payerSummary = payerSummary.rename(columns={"from": "Name"})

        ### cal everyone total receive
        receiverSummary = balanceDf.groupby("to")["total_amount"].sum().reset_index()
        receiverSummary["type"] = "receive"
        receiverSummary = receiverSummary.rename(columns={"to": "Name"})

        ### concat df
        finalSummary = pd.concat([payerSummary, receiverSummary], axis=0, ignore_index=True)

        ### modify df format
        finalSummary = finalSummary.groupby("Name").agg(
            total_received=pd.NamedAgg(column="total_amount", aggfunc=lambda x: x[finalSummary["type"] == "receive"].sum()),
            total_paid=pd.NamedAgg(column="total_amount", aggfunc=lambda x: x[finalSummary["type"] == "pay"].sum())
        ).reset_index()

        ### add Sum col
        finalSummary["Sum"] = finalSummary["total_received"] - finalSummary["total_paid"]

        return finalSummary

    def display_expenses(self):
        """
        顯示所有支出記錄
        """
        print("============= Total Payment Details =============")
        print(self.expensesDf)
        print("\n\n\n")

    def display_balances(self):
        """
        顯示結餘狀態
        """
        resultDf = self.make_bill_relation()
        balanceDf = self.cal_all_item_bill(resultDf)
        simplifiedDf = self.cal_simplified_balances(resultDf)
        finalSummary = self.cal_receive_pay_summary(balanceDf)

        self.expensesDf.to_csv("./raw_data.csv", encoding='utf_8_sig', index=False)

        ### print result
        print("============= Split Payment Details =============")
        prevName = None
        for _, row in balanceDf.iterrows():
            if prevName is None:
                prevName = row['from']

            if prevName == row['from']:
                print(f"{row['from']} pay {row['to']} {row['total_amount']} dollars, Items: {row['detailed_items']}")
            else:
                prevName = row['from']
                print("--------------------")
                print(f"{row['from']} pay {row['to']} {row['total_amount']} dollars, Items: {row['detailed_items']}")

        print("\n\n")

        print("============= Simplified Payment Details =============")
        prevName = None
        for _, row in simplifiedDf.iterrows():
            if prevName is None:
                prevName = row['from']

            if prevName == row['from']:
                print(f"{row['from']} pay {row['to']} {row['amount']} dollars")
            else:
                prevName = row['from']
                print("--------------------")
                print(f"{row['from']} pay {row['to']} {row['amount']} dollars")

        print("\n\n")

        print("============= Summary money =============")
        for _, row in finalSummary.iterrows():
            print(f"{row['Name']}, Balance {row['Sum']}, receive {row['total_received']}, pay {row['total_paid']} dollars")


# 主程式
if __name__ == "__main__":
    participants = ["Finn", "Will", "阿哲", "鴻瑋", "Ruby", "181", "帥哥", "佳詠"]  # 設置參與者
    splitter = ExpenseSplitter(participants)

    splitter.add_participant("HI")
    splitter.get_participant()

    print("============= Who join split bill =============")
    print(participants, "\n\n\n")

    ### add payment
    splitter.add_expense("阿哲", 250, "大林臭豆腐", ["Finn", "阿哲", "Ruby"])
    splitter.add_expense("阿哲", 320, "晚餐熱炒", ["Finn", "阿哲", "Ruby", "Will"])
    splitter.add_expense("阿哲", 50, "蒸餃", ["Finn", "阿哲", "Ruby"])
    splitter.add_expense("阿哲", 50, "涼麵", ["Will"])
    splitter.add_expense("阿哲", 25, "涼麵果汁", ["Ruby"])
    splitter.add_expense("阿哲", 105, "大林臭豆腐+大腸豬血湯", ["Finn", "Ruby"])
    splitter.add_expense("Will", 50, "馬鈴薯玉米筍", ["Finn", "阿哲", "Ruby", "Will"])
    
    splitter.add_expense("Ruby", 200, "螢火蟲門票", ["Finn", "阿哲", "Ruby", "Will"])
    splitter.add_expense("Ruby", 100, "咖哩", ["Finn", "阿哲", "Ruby", "Will"])
    splitter.add_expense("Ruby", 250, "抹茶芋頭捲", ["Finn", "Will", "阿哲", "鴻瑋", "Ruby", "181", "帥哥", "佳詠"])
    splitter.add_expense("Ruby", 760, "雞肉飯", ["Finn", "鴻瑋", "Ruby", "181", "帥哥", "佳詠"])
    splitter.add_expense("Ruby", 60, "酪梨牛奶", ["Finn"])
    splitter.add_expense("Ruby", 50, "鴨肉羹", ["Ruby", "Finn"])

    splitter.add_expense("Finn", 100, "炸物", ["Finn", "阿哲", "Ruby"])
    splitter.add_expense("Finn", 190, "鴨肉羹", ["Finn", "阿哲", "Ruby"])    
    splitter.add_expense("Finn", 800, "阿里山門票", ["Finn", "阿哲", "Ruby", "Will"])
    splitter.add_expense("Finn", 1126, "阿里山晚餐 - 葷", ["Finn", "阿哲", "鴻瑋", "Ruby", "181", "帥哥", "佳詠"])
    splitter.add_expense("Finn", 824, "阿里山晚餐 - 素", ["Finn", "Will", "阿哲", "鴻瑋", "Ruby", "181", "帥哥", "佳詠"])
    splitter.add_expense("Finn", 520, "鹹酥雞", ["Finn", "Will", "阿哲", "鴻瑋", "Ruby", "181", "帥哥", "佳詠"])
    splitter.add_expense("Finn", 180, "鴻瑋蛋糕", ["Finn", "Will", "阿哲", "Ruby", "181", "帥哥", "佳詠"])
    splitter.add_expense("Finn", 55, "雞肉飯", ["Finn", "鴻瑋"])
    splitter.add_expense("Finn", 100, "停車費", ["Finn", "阿哲", "Ruby", "Will"])
    splitter.add_expense("Finn", 1575, "油錢", ["Finn", "阿哲", "Ruby", "Will"])

    splitter.add_expense("鴻瑋", 13320, "兩天住宿", ["Finn", "Will", "阿哲", "鴻瑋", "Ruby", "181", "帥哥", "佳詠"])
    splitter.add_expense("佳詠", 40, "飲料", ["Finn"])

    # splitter.add_expense("Finn", 560, "油錢 (嘉義 -> 台北)", ["Finn", "阿哲", "Ruby", "Will"])
    # splitter.add_expense("Finn", 380, "油錢 (阿里山上下山)", ["Finn", "阿哲", "Ruby", "Will"])
    # splitter.add_expense("Finn", 635, "油錢 (台北 -> 嘉義)", ["Finn", "阿哲", "Ruby", "Will"])

    ### output result
    splitter.display_balances()
    print("\n\n\n")