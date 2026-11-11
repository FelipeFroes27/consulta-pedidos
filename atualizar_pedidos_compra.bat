@echo off
rem Atualiza a aba "Pedido de compra" com os dados do ERP Millennium.
rem Usado pelo Agendador de Tarefas do Windows. O log fica em logs\atualizacao.log
cd /d "%~dp0"
if not exist logs mkdir logs
set PYTHONIOENCODING=utf-8
"%~dp0venv\Scripts\python.exe" "%~dp0atualizar_pedidos_compra.py" >> "%~dp0logs\atualizacao.log" 2>&1
