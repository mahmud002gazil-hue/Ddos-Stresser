Stresser Layer 7

pip install aiohttp
python l7_stresser.py -url https://example.com/ -n 2000 -c 200

python l7_stresser.py -url https://example.com/login -m POST -d "user=admin&pass=123" -n 1000 -c 100
