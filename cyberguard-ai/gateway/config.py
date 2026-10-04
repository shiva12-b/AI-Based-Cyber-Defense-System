import os
from dotenv import load_dotenv
load_dotenv()
def env(k, d=""): return os.getenv(k, d)
def csv(k, d=""): return [x.strip() for x in env(k,d).split(',') if x.strip()]
