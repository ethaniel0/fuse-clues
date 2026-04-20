# *** clue 1: Wilkinson Terrace ***

```
/wilkinson/
  fourth_floor/
    terrace/
        table/
            napkin.txt
            receipt.txt
            coffee_cup.txt
        door/
            panel.txt
```


$ cat receipt.txt
```
Bseisu

Name: D. S.

Order:
- Large coffee
- No sugar

Pickup Time: 02:05

Order #53

```

$ cat coffee_cup.txt

```
"Life is like a chess puzzle. If you're stuck on a problem, start from the end"
```

$ cat napkin.txt
```
I knew this would happen.

If you're reading this, you made it to the terrace —
but you don't remember why.

The door isn’t broken.

I checked it already. The code to unlock is there,
just not where you expect it.
```

$ cat door/panel.txt

```
WILKINSON TERRACE ACCESS

status: locked

```

### Intended Solution
---
```
$ stat door/panel.txt
Size: 512        Modify: 03/04/2025 02:11:00
Mode: -rw-r--r-- Links: 1
Owner: root
```

```
$ dd if=door/panel.txt bs=1 skip=512
$ dd if=door/panel.txt bs=512 skip=1
code: 18

input not accepted from display

submit code directly to panel
```
- Coffee cup is important clue
- Order #53 is red herring
- Sets up for chess and Beisu
```
$ echo 18 > door/panel.txt
```
Changes: \
$ cat door/panel.txt

```
WILKINSON TERRACE ACCESS

status: unlocked

enter code: 556
```

--> fill in rest of Wilkinson

# *** clue 2: Beisu and Sorin ***

Relevant to this clue:
```
/wilkinson/
    first_floor/
        Bseisu/
            chess/
                note.txt
                board.txt
            counter/
                orders.txt
    fourth_floor/
        Office_403/
            white_board.txt
            desk/
                notes.txt
                Duke_Card.pass
        terrace/
            -
```
#### Desk contents hidden/locked, need to access
```
$ ls -l
-rw-r--r--  root  root   312  white_board.txt
d---------  root  root  4096  desk/
```
---
---
$ cat orders.txt
```
Bseisu Orders — 03/04

02:01 — Andrew Hilton — latte
02:03 — John Board — espresso
02:05 — Daniel Sorin — coffee
02:06 — Tyler Bletsch — tea
```

$ cat chess_board.txt
```
8  r . . . k . . r
7  p p p . . p p p
6  . . . . . . . .
5  . . . . . . . .
4  . . . Q . . . .
3  . . . . . . . .
2  P P P . . P P P
1  R . . . K . . R

   a b c d e f g h
```

$ cat chess/note.txt
```
Try and solve this mate-in-two while waiting for your order!

Regulars have been arguing about the solution all morning.
Below, they each wrote down their answer and where to find them.

- d5   , Qd2       — 109
- Nc3  , Nd5       — 110
- Qd8+ , Rxd8      — 403
- Qe4  , Qxe5      — 411
```
$ cat white_board.txt
```
Error Correction — Hamming Code (7,4)

received word:
1011110

parity checks:
p1 -> FAIL
p2 -> OK
p4 -> FAIL

fix the error directly
```

## Intended solution

- write to specific offset with correct value, using vim etc

- opens up desk/

$ cat notes.txt
```
Need to go back down to the garage lab.

Panel’s still miswired.
It wasn’t the terminals — the lengths were off.

They trimmed the documentation again.
Have to check the full read, not just what shows up.

Don’t redo everything. Just fix the bad parts.

Card reader should still accept manual entry.
```

$ cat Duke_Card.pass
```
!d=NFkXKeWu^HTSw
```

# *** clue 3:  ***
### GET WIRES AND WIRE_CUTTER FROM HUDSON!
```
/wilkinson/first_floor/garage_lab/
  reader.txt
  docs/
    offset_guide.txt
    terminal_map.txt
    repair_log.txt
  bench/
    <!-- red_wire.txt
    blue_wire.txt
    green_wire.txt
    wire_cutter -->
  panel/
    terminal_A/
    terminal_B/
    terminal_C/
  locker/
    (hidden)
```

$ cat reader.txt
```
DUKE CARD READER

status: offline
manual override available
```

#### intended solution
$ cat ../../fourth_floor/Office_403/desk/Duke_Card.pass > reader.txt

$ cat repair_log.txt
```
GARAGE LAB REPAIR LOG

The panel keeps failing because the replacement leads
were cut wrong and routed by sticker instead of by spec.

Don’t trust the labels.
Verify positions.
Trim first.
Route second.
```

$ cat offset_guide.txt
```
Replacement leads came in mislabeled again.

Verification positions from last batch:
R at 5
G at 12
B at 8

Trim only after verification.
```


$ cat bench/*_wire.txt
```
red lead
sticker: 73
factory length: 20
---
green lead
sticker: 11
factory length: 15
---
blue lead
sticker: 42
factory length: 25
```

hidden
```
$ dd if=bench/red_wire.txt bs=1 skip=5
→ 12

$ dd if=bench/green_wire.txt bs=1 skip=12
→ 8

$ dd if=bench/blue_wire.txt bs=1 skip=8
→ 14
```

cut wires
```
truncate -s 12 bench/red_wire.txt
truncate -s 8 bench/green_wire.txt
truncate -s 14 bench/blue_wire.txt
```

$ cat terminal_map.txt
```
Terminal routing reference

A : 73
B : 11
C : 42
```

move wires
```
$ mv bench/red_wire.txt panel/terminal_A/
$ mv bench/green_wire.txt panel/terminal_B/
$ mv bench/blue_wire.txt panel/terminal_C/
```

NOW LOCKER IS OPEN
```
  locker/
    factorio_notes.txt
```

$ cat factorio_notes.txt
```
RAID access logs don’t line up.

Looks like a normal student job at first,
but the IP isn’t stable.

Same capture → different result depending how it’s read.

That shouldn’t happen.

Saved the raw output.
Didn’t get to clean it.

- A.H
```


# *** clue 4: Hilton's Office ***

```
/wilkinson/
  first_floor/
    Office_103/
        terminal/
            README.txt
            board.txt
        computer/
            (locked — requires puzzle solved)
```

---

```
$ cat README.txt
```
```
OFFICE 109 — RESEARCH TERMINAL

This machine is locked to a single session.
Previous user left mid-session and the auth state corrupted.

Recovery mode is active.
The system will restore access once the session puzzle is resolved.
```

---

```
$ cat board.txt
```
```
SESSION RECOVERY — PUZZLE ACTIVE

+---+---+---+
| 7 | 2 | 4 |
+---+---+---+
| 5 |   | 6 |
+---+---+---+
| 8 | 3 | 1 |
+---+---+---+

Enter a direction to play
```

---

```
$ echo up > board.txt
$ cat board.txt
```
```
SESSION RECOVERY — PUZZLE ACTIVE

+---+---+---+
| 7 | 2 | 4 |
+---+---+---+
| 5 | 3 | 6 |
+---+---+---+
| 8 |   | 1 |
+---+---+---+

Enter a direction to play
```

---

On solve:

```
$ cat board.txt
```
```
SESSION RECOVERED

+---+---+---+
| 1 | 2 | 3 |
+---+---+---+
| 4 | 5 | 6 |
+---+---+---+
| 7 | 8 |   |
+---+---+---+


authentication restored
access granted to: computer/

> terminal unlocked
```

SOLUTION
```
1: DOWN
2: RIGHT
3: UP
4: LEFT
5: LEFT
6: UP
7: RIGHT
8: RIGHT
9: DOWN
10: LEFT
11: DOWN
12: LEFT
13: UP
14: RIGHT
15: UP
16: LEFT
17: DOWN
18: RIGHT
19: RIGHT
20: DOWN
```

---

```
$ ls computer/
  hilton_logs.tar.gz
  session_notes.txt
```

```
$ cat session_notes.txt
```
```
Andrew Hilton — session notes 03/04

Been seeing unusual access patterns on the RAID array all week.
Student job accounts, but the timing is off.

Dumped the raw access logs before I left. File got large fast
so I compressed them.

If something looks wrong, Bletsch would know.
He set up the monitoring system. Office 110.

— A.H.
```

```
$ tar -xzf hilton_logs.tar.gz
$ ls
  access.log
```

---

### Intended Solution Path

```
player enters Office 109
reads README.txt → understands single-file mechanic
reads board.txt → sees scrambled puzzle and prompt
iteratively writes directions to board.txt
solves 8-puzzle → computer/ unlocks
reads session_notes.txt → directed to Bletsch, Office 103
extracts hilton_logs.tar.gz → gets noisy access.log
carries access.log into clue 5
```

---

# **Clue 5 — Bletsch / RAID Analysis**


```
/wilkinson/
  first_floor/
    Office_103/
        desk/
            notes.txt
            filter_draft.txt
        terminal/
            status.txt
  fifth_floor/
    graduate_student_lounge/
        table/
            analysis_action.txt
            analysis_time.txt
            analysis_job.txt
            analysis_flag.txt
            analysis_auth.txt
        whiteboard.txt
```

**Answer:** `src:243.69`

```bash
grep "02:05" access.log \
| grep "job:student" \
| grep -v "auth:ok" \
| grep "flag:" \
| grep "action:read"
```

---

## **Key steps:**

* Identify filtering strategy from Bletsch + lounge notes:

  * isolate **time window**
  * isolate **job type**
  * remove **common behavior (auth:ok)**
  * isolate **flagged entries**
  * narrow to **read actions**

* Build filter step-by-step

* Final result:

  ```text
  [02:05:17] job:student src:243.69 target:RAID-A action:read_direct auth:override flag:UNPROTECTED
  ```

* Extract IP source address:

  ```
  src:243.69
  ```
