# Every command from README.md 'Usage', run in order with my-trip.json -> <tmp>/my-trip.json
$ python3 -m tripsplit --file my-trip.json person Aru
Added Aru
exit=0
$ python3 -m tripsplit --file my-trip.json person Dana
Added Dana
exit=0
$ python3 -m tripsplit --file my-trip.json person Timur
Added Timur
exit=0
$ python3 -m tripsplit --file my-trip.json add "Taxi" 90 Aru
Added Taxi (90.00)
exit=0
$ python3 -m tripsplit --file my-trip.json add "Hotel" 200 Dana --split percent --weights "Aru=50,Dana=25,Timur=25"
Added Hotel (200.00)
exit=0
$ python3 -m tripsplit --file my-trip.json list
Taxi: 90.00 paid by Aru -> Aru 30.00, Dana 30.00, Timur 30.00
Hotel: 200.00 paid by Dana -> Aru 100.00, Dana 50.00, Timur 50.00
exit=0
$ python3 -m tripsplit --file my-trip.json balance
Aru        -40.00
Dana       +120.00
Timur      -80.00
exit=0
$ python3 -m tripsplit --file my-trip.json settle
Timur -> Dana: 80.00
Aru -> Dana: 40.00
exit=0
# README 'Checks' commands are in final-checks.txt
