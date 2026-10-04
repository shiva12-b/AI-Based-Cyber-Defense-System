import os
import threading
import uvicorn

def run_bank():
    uvicorn.run('bank_server.main:app', host='127.0.0.1', port=int(os.getenv('BANK_PORT','9000')), log_level='info')

if __name__ == '__main__':
    bank_port=int(os.getenv('BANK_PORT','9000'))
    os.environ.setdefault('BANK_SERVER_URL', f'http://127.0.0.1:{bank_port}')
    gateway_port=int(os.getenv('PORT',os.getenv('GATEWAY_PORT','8000')))
    threading.Thread(target=run_bank,daemon=True).start()
    uvicorn.run('gateway.main:app',host='0.0.0.0',port=gateway_port,log_level='info')
