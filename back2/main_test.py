from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from splitter import ExpenseSplitter


"""
python -m uvicorn main_test:app --reload
"""

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

splitter = ExpenseSplitter(participants=[])

### Home
@app.get("/", response_class=HTMLResponse)
def get_home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "participants": splitter.get_participant(),
        "expenses": splitter.expensesDf.to_dict(orient="records")
    })

### Add user
@app.post("/add_user", response_class=RedirectResponse)
def add_user(request: Request, participant: str = Form(...)):
    splitter.add_participant(participant)
    return RedirectResponse(url="/", status_code=303)

### delete user
@app.post("/delete_user", response_class=RedirectResponse)
def delete_user(request: Request, participant: str = Form(...)):
    splitter.delete_participant(participant)
    return RedirectResponse(url="/", status_code=303)

### get user
@app.get("/get_user")
def get_user():
    userList = splitter.get_participant()
    return JSONResponse(content={"users": userList})


### Add payments
@app.post("/add_bill", response_class=RedirectResponse)
def add_bill(
    request: Request,
    payer: str = Form(...),
    amount: float = Form(...),
    item: str = Form(...),
    participants: list[str] = Form(...)
):
    splitter.add_expense(payer, amount, item, participants)
    return RedirectResponse(url="/", status_code=303)


### delete user
@app.post("/delete_bill", response_class=RedirectResponse)
def delete_bill(request: Request, idx: int = Form(...)):
    splitter.delete_expense(idx)
    return RedirectResponse(url="/", status_code=303)

### get bill
@app.get("/get_bill")
def get_bill():
    df = splitter.get_expense()
    return JSONResponse(content={"users": df.to_dict(orient="records")})