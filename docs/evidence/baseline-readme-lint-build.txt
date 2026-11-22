$ pip install -r requirements.txt   (README step; not run: would install an unpinned package)
$ pytest   (README test command)
(eval):1: command not found: pytest
exit=127
$ python3 -m pytest
/Library/Developer/CommandLineTools/usr/bin/python3: No module named pytest
exit=1
$ python3 main.py balance   (README usage)
/Library/Developer/CommandLineTools/usr/bin/python3: can't open file '~/code/uni/swe/L5/yeraliyeva-anel/main.py': [Errno 2] No such file or directory
exit=2
$ python3 -m compileall -q tripsplit tests   (only available "build"/syntax check)
exit=0
$ ruff / flake8 / mypy available?
ruff: yes
flake8: not installed
mypy: not installed
$ python3 -m tripsplit --file data/trip.json list
Train tickets: 100.00 paid by Aru -> Aru 33.33, Dana 33.33, Timur 33.33
Guesthouse: 240.00 paid by Dana -> Aru 96.00, Dana 72.00, Timur 72.00
Dinner: 75.50 paid by Timur -> Aru 25.17, Dana 25.17, Timur 25.17
$ python3 -m tripsplit --file data/trip.json balance
Aru        -54.50
Dana       +109.50
Timur      -55.00
