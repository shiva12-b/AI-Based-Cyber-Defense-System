import sqlite3, json
from datetime import datetime, timezone
from .config import env

def db_path():
    u=env('DATABASE_URL','sqlite:///./cyberguard.db')
    if not u.startswith('sqlite:///'): raise RuntimeError('This demo build currently requires DATABASE_URL=sqlite:///...')
    return u[len('sqlite:///'):]
def conn():
    c=sqlite3.connect(db_path(), check_same_thread=False); c.row_factory=sqlite3.Row; return c
def now(): return datetime.now(timezone.utc).isoformat()
def init():
    c=conn(); c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,name TEXT NOT NULL,role TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,account_no TEXT UNIQUE NOT NULL,balance REAL NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS beneficiaries(id TEXT PRIMARY KEY,owner_user_id TEXT NOT NULL,beneficiary_account_id TEXT NOT NULL,nickname TEXT,created_at TEXT NOT NULL,UNIQUE(owner_user_id,beneficiary_account_id));
    CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,device_name TEXT NOT NULL,trusted INTEGER NOT NULL DEFAULT 1,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,device_id TEXT NOT NULL,created_at TEXT NOT NULL,last_seen TEXT NOT NULL,status TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,ts TEXT NOT NULL,user_id TEXT,device_id TEXT,session_id TEXT,type TEXT NOT NULL,data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY,ts TEXT NOT NULL,from_account TEXT,to_account TEXT,amount REAL,status TEXT NOT NULL,reason TEXT,request_id TEXT);
    CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,ts TEXT NOT NULL,user_id TEXT,device_id TEXT,session_id TEXT,method TEXT,path TEXT,request_type TEXT,payload TEXT,risk_score INTEGER,risk_level TEXT,decision TEXT,reason TEXT,forwarded INTEGER,bank_status TEXT);
    CREATE TABLE IF NOT EXISTS incidents(id TEXT PRIMARY KEY,request_id TEXT NOT NULL,created_at TEXT NOT NULL,status TEXT NOT NULL,classification TEXT,risk_score INTEGER,confidence INTEGER,summary TEXT,recommendation TEXT,evidence TEXT,ai_report TEXT);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,ts TEXT NOT NULL,request_id TEXT,event TEXT,detail TEXT);
    '''); c.commit(); c.close()
def execute(sql,args=()):
    c=conn(); cur=c.execute(sql,args); c.commit(); x=cur.lastrowid; c.close(); return x
def one(sql,args=()):
    c=conn(); r=c.execute(sql,args).fetchone(); c.close(); return dict(r) if r else None
def rows(sql,args=()):
    c=conn(); r=[dict(x) for x in c.execute(sql,args).fetchall()]; c.close(); return r
def j(x): return json.dumps(x,default=str)
