Nume: Iancu George
Grupă: 332CC

# Tema 1 ASC - Marketplace

Organizare
-

În cadrul acestei teme am implementat un Marketplace prin intermediul căruia mai mulți ***producători*** își oferă produsele spre vânzare, iar mai mulți ***consumatori*** achiziționează produsele puse la dispoziție.

***Producător:***
* există mai mulți producători ce produc obiecte de tip ceai/cafea;
* fiecare producător poate adăuga un număr limitat de produse;
* atunci când această limită este atinsă, producătorul așteaptă până când este vândut cel puțin un produs de al său.

***Consumator:***
* fiecare consumator are nevoie de un coș de cumpărături, cu un id asociat;
* poate adăuga produse în coș: produsele respective devin indisponibile pentru ceilalți clienți;
* poate șterge produse din coș: produsele respective redevin disponibile pentru toți consumatorii;
* poate plasa o comandă: produsele rezervate vor fi eliminate din lista de produse ale producătorilor.

Pentru a implementa aceste funcționalități, am avut următoarea abordare:
* pentru a înregistra un producător sau un coș de cumpărături, avem câte un contor, pe baza căruia o să generăm id-urile corespunzătoare. De asemenea, fiind vorba de paralelism, mai multe thread-uri ar putea modifica simultan aceste valori, astfel, am folosit două obiecte Lock(), pentru a evita race conditions;
* pentru a reține numărul de produse publicate și nevândute încă de fiecare producător, folosim un dicționar, având key: id-ul producătorului și value: numărul de produse publicate și nevândute încă de acest producător. Deoarece aceste numere pot fi modificate atât de producător (prin publicarea de produse), cât și de consumatori (prin plasarea comenzilor), am folosit încă un dicționar, în care fiecărui id de producător îi este asociat un Lock();
* pentru conceptul de produs disponibil și indisponibil, am folosit un dicționar, având key: numele produsului și value: lista id-urilor de producători care au acest produs disponibil (lista poate conține duplicate, dacă un producător are mai multe unități disponibile);
* pentru coșurile de cumpărături am folosit un dicționar, având key: id-ul coșului și value: lista ce reprezintă coșul de cumpărături, explicată mai jos;
* coșul de cumpărături este o listă de dicționare, de forma: {"product": produsul, "producer_id": id-ul producătorului}. Astfel, atunci când un consumator rezervă un produs, o să știe de la ce producător a rezervat, iar id-ul producătorului o să fie șters din lista de producători ce au produsul disponibil. Apoi, dacă consumatorul dorește să șteargă un produs din coș, pe baza informației salvate, o să putem readăuga id-ul producătorului în lista de producători care au produsul disponibil. Această informație ne este utilă și atunci când un consumator plasează o comandă, deoarece o să știm pentru ce producători trebuie să reducem numărul de produse nevândute încă;
* deși anumite operații pe liste sunt Thread-Safe, o succesiune de astfel de operații nu este neapărat Thread-Safe. Astfel, pentru listele de producători care au un anumit produs disponibil, am folosit Lock-uri, fiind explicat și în comentariile codului sursă.

Consider tema utilă pentru că m-am obișnuit cu coding style-ul din Python, cu sintaxa de Python și pentru partea de Unit Testing.
Totuși, mi se pare că se pierde din farmecul Multithreading-ului prin folosirea apelurilor sleep, în locul unor elemente de sincronizare.

Consider implementarea ok, dar sigur se putea și mai bine.

Implementare
-

* întregul enunț al temei este implementat;
* cred că am verificat niște condiții extra (de exemplu: atunci când un produs este șters din coș, verific dacă produsul exista pentru început în coș);
* a trebuit să regândesc implementarea: prima dată implementasem cozile pentru produsele producătorilor, folosind și niște flag-uri pentru disponibilitate, plus că atunci când un consumator dorea să adauge un produs în coș, căutam produsul la toți producătorii, până îl găseam. Local îmi mergeau toate testele, dar pe vmchecker luam timeout pe ultimul test.

Resurse utilizate
-

* documentația pentru Python (în mare parte link-urile din enunțul temei);
* laboratoarele 1-3 de ASC de pe OCW;
* probabil StackOverflow când aveam vreo eroare.

Git
-
Link către repository-ul de git: [https://github.com/JorJ14/tema1_asc.git]() (momentan privat).

