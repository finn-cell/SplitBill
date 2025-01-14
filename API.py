from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

class ExpenseSplitter:
    def __init__(self, participants, digit=0):
        self.digit = digit
        self.participants = participants
        columns = ['payer', 'amount', 'item'] + participants + ['pay_' + name for name in participants]
        self.expensesDf = pd.DataFrame(columns=columns)
        self.billDf = pd.DataFrame(0, index=participants, columns=participants)
    
    def add_expense(self, payer, amount, item, participants):
        peopleCont = 0
        expenseData = {'payer': [payer], 'amount': [amount], 'item': [item]}
        for participant in self.participants:
            if participant in participants:
                expenseData[participant] = [1]
                peopleCont += 1
            else:
                expenseData[participant] = [0]
        
        if self.digit == 0:
            money = int(expenseData['amount'][0] / peopleCont)
        else:
            money = round(expenseData['amount'][0] / peopleCont, self.digit)

        for participant in self.participants:
            if participant in participants:
                expenseData['pay_' + participant] = [money]
            else:
                expenseData['pay_' + participant] = [0]

        self.expensesDf = pd.concat([self.expensesDf, pd.DataFrame(expenseData)], ignore_index=True)

    def calculate_balances(self):
        paymentsBlanceDf = pd.DataFrame()
        for payer, tmpDf in self.expensesDf.groupby(['payer']):
            for person in self.participants:
                paymentsBlanceDf[person] = tmpDf[f"pay_{person}"].sum()

        transactions = []
        for _, row in self.expensesDf.iterrows():
            payer = row["payer"]; item = row["item"]
            for person in self.participants:
                amountToPay = row[f"pay_{person}"]
                transactions.append({"from": person, "to": payer, "amount": amountToPay, "item": item})
        resultDf = pd.DataFrame(transactions)
        resultDf = resultDf[resultDf["amount"] > 0]
        
        balanceDf = (
            resultDf.groupby(["from", "to"])
                .apply(lambda group: pd.Series({
                "total_amount": group["amount"].sum(),
                "detailed_items": self.aggregate_items(group),
            })).reset_index()
        )
        return balanceDf

    def aggregate_items(self, group):
        itemsSummary = {}
        for _, row in group.iterrows():
            item = row["item"]
            amount = row["amount"]
            if item in itemsSummary:
                itemsSummary[item] += amount
            else:
                itemsSummary[item] = amount
        return ", ".join(f"{item}: {amount}" for item, amount in itemsSummary.items())


# 初始化分帳程式
expense_splitter = ExpenseSplitter(participants=["Alice", "Bob", "Charlie"])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    payer = request.form.get('payer')
    amount = float(request.form.get('amount'))
    item = request.form.get('item')
    participants = request.form.getlist('participants')

    expense_splitter.add_expense(payer, amount, item, participants)
    return jsonify({"message": "Expense added successfully!"})

@app.route('/calculate_balances', methods=['GET'])
def calculate_balances():
    balanceDf = expense_splitter.calculate_balances()
    return jsonify(balanceDf.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
