from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from splitter import ExpenseSplitter
import pandas as pd

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

splitter = ExpenseSplitter(participants=[])

# ------------------------------
# Root - Redirect to summary
# ------------------------------
@app.get("/")
def root():
    return RedirectResponse("/summary")

# ------------------------------
# User Management Page
# ------------------------------
@app.get("/users", response_class=HTMLResponse)
def show_users(request: Request):
    return templates.TemplateResponse("users.html", {
        "request": request,
        "participants": splitter.get_participant()
    })

@app.post("/add_user")
def add_user(participant: str = Form(...)):
    splitter.add_participant(participant)
    return RedirectResponse("/users", status_code=303)

@app.post("/delete_user")
def delete_user(participant: str = Form(...)):
    splitter.delete_participant(participant)
    return RedirectResponse("/users", status_code=303)

# ------------------------------
# Add Bill Page
# ------------------------------
@app.get("/add_bill", response_class=HTMLResponse)
def show_add_bill(request: Request):
    return templates.TemplateResponse("add_bill.html", {
        "request": request,
        "participants": splitter.get_participant(),
        "expenses": splitter.expensesDf.to_dict(orient="records")
    })

@app.post("/add_bill")
def add_bill(
    payer: str = Form(...),
    amount: float = Form(...),
    item: str = Form(...),
    participants: list[str] = Form(...)
):
    splitter.add_expense(payer, amount, item, participants)
    return RedirectResponse("/add_bill", status_code=303)

@app.post("/delete_bill")
def delete_bill(idx: int = Form(...)):
    splitter.delete_expense(idx)
    return RedirectResponse("/add_bill", status_code=303)

# ------------------------------
# Edit Bill Page
# ------------------------------
@app.get("/edit_bill/{idx}", response_class=HTMLResponse)
def edit_bill(request: Request, idx: int):
    if idx >= len(splitter.expensesDf):
        return RedirectResponse("/add_bill", status_code=303)

    record = splitter.expensesDf.iloc[idx].to_dict()
    participants = splitter.get_participant()
    checked = [p for p in participants if record.get(p) == 1]

    return templates.TemplateResponse("edit_bill.html", {
        "request": request,
        "idx": idx,
        "record": record,
        "participants": participants,
        "checked": checked
    })

@app.post("/update_bill/{idx}")
def update_bill(
    idx: int,
    payer: str = Form(...),
    amount: float = Form(...),
    item: str = Form(...),
    participants: list[str] = Form(...)
):
    splitter.delete_expense(idx)
    splitter.add_expense(payer, amount, item, participants)
    return RedirectResponse("/add_bill", status_code=303)

# ------------------------------
# Summary Page
# ------------------------------
@app.get("/summary", response_class=HTMLResponse)
def show_summary(request: Request):
    if splitter.expensesDf.empty:
        summary_df = pd.DataFrame(columns=["Name", "total_received", "total_paid", "Sum"])
        simplified_df = pd.DataFrame(columns=["from", "to", "amount"])
    else:
        result_df = splitter.make_bill_relation()
        balance_df = splitter.cal_all_item_bill(result_df)
        summary_df = splitter.cal_receive_pay_summary(balance_df)
        simplified_df = splitter.cal_simplified_balances(result_df)

    return templates.TemplateResponse("summary.html", {
        "request": request,
        "summary": summary_df.to_dict(orient="records"),
        "simplified": simplified_df.to_dict(orient="records")
    })

# ------------------------------
# Detailed Split Page
# ------------------------------
@app.get("/details", response_class=HTMLResponse)
def show_details(request: Request):
    if splitter.expensesDf.empty:
        detailed_df = pd.DataFrame(columns=["from", "to", "amount", "item"])
    else:
        detailed_df = splitter.make_bill_relation()

    return templates.TemplateResponse("details.html", {
        "request": request,
        "details": detailed_df.to_dict(orient="records")
    })

# ------------------------------
# Bill Detail by Index
# ------------------------------
@app.get("/bill_detail/{idx}", response_class=HTMLResponse)
def bill_detail(request: Request, idx: int):
    if idx >= len(splitter.expensesDf):
        return RedirectResponse("/add_bill", status_code=303)

    row = splitter.expensesDf.iloc[idx]
    payer = row["payer"]
    item = row["item"]
    amount = row["amount"]

    # 取得每位參與者應付金額
    details = []
    for person in splitter.participants:
        paid = row.get(f"receive_from_{person}", 0)
        if row.get(person, 0) == 1:
            details.append({"participant": person, "amount": paid})

    return templates.TemplateResponse("bill_detail.html", {
        "request": request,
        "idx": idx,
        "item": item,
        "payer": payer,
        "amount": amount,
        "details": details
    })
