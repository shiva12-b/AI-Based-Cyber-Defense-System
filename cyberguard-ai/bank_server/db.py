import sqlite3,os
from datetime import datetime,timezone
from pathlib import Path
DB=Path(os.getenv('BANK_DATABASE_PATH','./bank.db'))
def conn(): c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row; return c
def now(): return datetime.now(timezone.utc).isoformat()
def init():
 c=conn(); c.executescript('''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,name TEXT,role TEXT,password_hash TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY,user_id TEXT,account_no TEXT UNIQUE,balance REAL,status TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS beneficiaries(id TEXT PRIMARY KEY,owner_user_id TEXT,beneficiary_account_id TEXT,nickname TEXT,created_at TEXT,UNIQUE(owner_user_id,beneficiary_account_id));CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY,ts TEXT,from_account TEXT,to_account TEXT,amount REAL,status TEXT,reason TEXT,request_id TEXT);'''); c.commit(); c.close()
def execute(s,a=()): c=conn(); x=c.execute(s,a).lastrowid;c.commit();c.close();return x
def one(s,a=()): c=conn();r=c.execute(s,a).fetchone();c.close();return dict(r) if r else None
def rows(s,a=()): c=conn();r=[dict(x) for x in c.execute(s,a).fetchall()];c.close();return r
