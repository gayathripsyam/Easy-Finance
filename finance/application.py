from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    s=session["user_id"]
    irows=db.execute("SELECT * from portfolio where id=:id",id=s)
    irows3=db.execute("SELECT count(symbol) from portfolio where id=:id", id=s)
    n=irows3[0]['count(symbol)']

    for i in range(0,n):
        a=irows[i]["symbol"]
        b=lookup(a)
        if b==None:

            return apology("Quote error")

        sh=irows[i]["shares"]
        c=b['price']
        totaln=sh*c
        db.execute("UPDATE portfolio set price=:price where symbol=:symbol and id=:id", price=c,  symbol=a, id=s)
        db.execute("UPDATE portfolio set total=:total where symbol=:symbol and id=:id", total=totaln, symbol=a, id=s)

    irows2=db.execute("SELECT * from portfolio where id=:id",id=s)
    irows4=db.execute("SELECT sum(total) from portfolio where id=:id",id=s)
    e=irows4[0]['sum(total)']
    irows5=db.execute("SELECT cash from users where id=:id",id=s)
    f=irows5[0]['cash']
    if e:
        g=e+f
        return render_template("index.html", rows=irows2, gross=usd(round(g,2)), cash=usd(round(f,2)))
    if not e:
        return render_template("index.html", rows=irows2, cash=usd(round(f,2)))





@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method=="POST":
        bs=request.form.get("bsymbol")
        bs=bs.upper()
        bsh=int(request.form.get("bshares"))
        ba=lookup(bs)
        if ba!= None and int(bsh)>0:
            ncash=float(bsh)*ba['price']
            c=session["user_id"]
            brow= db.execute("SELECT * FROM users WHERE id = :id", id=c)
            if brow:
                if ncash<=brow[0]["cash"]:
                    db.execute("INSERT INTO history(id,symbol,name,shares,price,total) VALUES(:id,:symbol,:name,:shares,:price,:total)", id=c, symbol=bs,
                    name=bs, shares=bsh, price=ba['price'],total=ncash)
                    brow2=db.execute("SELECT sum(shares) from history where id=:id and symbol=:symbol", id=c, symbol=bs)
                    zz=brow2[0]["sum(shares)"]
                    total2=float(zz)*ba['price']
                    db.execute("INSERT OR REPLACE INTO portfolio(id,symbol,name,shares,price,total) values(:id,:symbol,:name,:shares,:price,:total)",
                    id=c, symbol=bs, name=bs, shares=zz,price=ba['price'],total=total2)

                    nncash=brow[0]["cash"]-ncash
                    nrcash=usd(round(nncash,2))
                    db.execute("UPDATE users set cash=:cash where id=:id", cash=nncash, id=c)
                    return redirect(url_for("index"))
                else:
                    return apology("Not enough Funds")
            else:
                return apology("Log in again")







        else:
            return apology("Invalid stock symbol or shares")



    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    c=session["user_id"]
    rows=db.execute("SELECT * FROM history where id=:id", id=c)
    return render_template("history.html", rows=rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))


        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]


        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method=="POST":
        a=request.form.get("symbol")
        b=lookup(a)
        if(a==""):
            return apology("INVAID SYMBOL")

        if b:
            c=a
            d=usd(b['price'])
            return render_template("quoted.html", quote=c, price=d)
        else:
            return apology("INVAID SYMBOL",a)


    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    session.clear()
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
        elif not request.form.get("confirm"):
            return apology("must confirm password")
        a=request.form.get("password")
        e=request.form.get("username")
        b=request.form.get("confirm")
        d=db.execute("SELECT * FROM users WHERE username = :username", username=e)

        if a!=b:
            return apology("Passwords do not match")
        elif len(d)!=0:
            return apology("Username exists")
        else:
            c=pwd_context.hash(a)
            db.execute("INSERT INTO users(username,hash) VALUES(:username, :hash)", username=request.form.get("username"),hash=c)
            f=db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
            session["user_id"]=f[0]["id"]
            return redirect(url_for("index"))
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method=="POST":
        sa=request.form.get("ssymbol")
        sb=int(request.form.get("sshares"))
        sc=session["user_id"]
        srows=db.execute("SELECT * from portfolio where id=:id and symbol=:symbol", id=sc, symbol=sa)
        srows2=db.execute("SELECT cash from users where id=:id ", id=sc)
        oldcash=srows2[0]['cash']

        if srows:
            sd=srows[0]['shares']


            if sb <=sd:

                se=lookup(sa)
                sf=se['price']
                sg=sf*sb
                sh=sd-sb
                si=sh*sf
                newcash=oldcash+sg
                db.execute("INSERT INTO history(id,symbol,name,shares,price,total) VALUES(:id,:symbol,:name,:shares,:price,:total)", id=sc, symbol=sa,
                        name=sa, shares=-sb, price=sf,total=sg)
                db.execute("update users set cash=:cash where id=:id ",cash=newcash, id=sc)
                if sb!=sd:
                    db.execute("update portfolio set price=:price where id=:id and symbol=:symbol",price=sf, id=sc, symbol=sa)
                    db.execute("update portfolio set shares=:shares where id=:id and symbol=:symbol",shares=sh, id=sc, symbol=sa)
                    db.execute("update portfolio set total=:total where id=:id and symbol=:symbol",total=si, id=sc, symbol=sa)


                    return redirect(url_for("index"))
                else:
                    db.execute("delete from portfolio where id=:id and symbol=:symbol", id=sc, symbol=sa)
                    return redirect(url_for("index"))

            else:
                return apology("You dont have enough stocks")
        else:
            return apology("You dont own any stocks of current company")

    else:
        return render_template("sell.html")


@app.route("/addmoney", methods=["GET", "POST"])
@login_required
def addmoney():
    if request.method=="POST":
        a=int(request.form.get("money"))
        if a>0:
            c=session["user_id"]
            row=db.execute("SELECT cash from users where id=:id", id=c)
            oldcash=row[0]['cash']
            newcash=oldcash+a
            db.execute("UPDATE users SET cash=:cash where id=:id", cash=newcash, id=c)
            return render_template("addmoney2.html", am=usd(a), total=usd(newcash))
        else:
            return apology("Enter valid money")
    else:
        return render_template("addmoney.html")
