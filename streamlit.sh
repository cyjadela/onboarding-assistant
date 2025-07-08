#!/bin/bash
echo "패키지 설치 시작..."
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
echo "패키지 설치 완료!"
echo "Streamlit 시작..."
python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0