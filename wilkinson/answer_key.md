# **Clue 1 — Wilkinson Terrace**

**Answer:** `echo 18 > fourth_floor/terrace/door/panel.txt`

**Key steps:**

* Hidden data in `door/panel.txt` beyond visible content
    * `coffee_cup.txt` provides the hint to look (read) from the end
* Check file size of panel (512) and extract using it as offset:
```
  dd if=door/panel.txt bs=1 skip=512
```
* Reveals:
```
 code: 18

 submit code to panel
```

* Submit to panel

```
 echo 18 > fourth_floor/terrace/door/panel.txt
```

---

# **Clue 2 — Beisu & Sorin / Office 403**

**Answer:** 
```
vim fourth_floor/Office_403/white_board.txt
Change `1011110` to `1011010` (flip fifth bit)
```

**Key steps:**

* Terrace leaves clues instructing you to go see Bseisu and interact with chess board
* We want to find the person with initials D.S, ordered coffee, and left a hint involving chess
* The note in Bseisu says the person good at chess is in office 403
* The white_board in Office_403 has a hamming code puzzle to solve to access contents of `desk\`
* Given: `1011110` and parity failures: `p1`, `p4`
* The error position is the fifth bit
* Need to use Vim to directly only change that bit
* Apply fix → desk unlocks

**Result:**

* Access to:

  ```
  notes.txt
  Duke_Card.pass = !d=NFkXKeWu^HTSw
  ```

---

# **Clue 3 — Garage Lab Wiring**

**Answer:**
First gain access to garage lab using `Duke_Card.pass`:
```
cat fourth_floor/Office_403/desk/Duke_Card.pass > first_floor/garage_lab/card_reader.txt
```
Then obtain wires and wire_cutter from Hudson through the second floor portal!
```
mv second_floor/portal/red_wire first_floor/garage_lab/bench/
mv second_floor/portal/green_wire first_floor/garage_lab/bench/
mv second_floor/portal/blue_wire first_floor/garage_lab/bench/
mv second_floor/portal/wire_cutter first_floor/garage_lab/bench/
```
Cut (truncate) the wires to appropriate length based on offset_guide
```
  truncate -s 12 red
  truncate -s 8 green
  truncate -s 14 blue
```
Then route (mv) the files to appropriate terminals on the panel
```
mv bench/red_wire panel/terminal_A/
mv bench/green_wire panel/terminal_B/
mv bench/blue_wire panel/terminal_C/
```

**Result:**

* Locker opens → `factorio_notes.txt`

---

# **Clue 4 — Hilton Office Puzzle**

**Answer:**

Insert directions in this order to `game.puzzle`
```
UP
LEFT
DOWN
RIGHT
RIGHT
DOWN
LEFT
LEFT
UP
RIGHT
UP
RIGHT
DOWN
LEFT
DOWN
RIGHT
UP
LEFT
LEFT
UP
```

**Result:**

* Unlocks `computer/`
 ```
 hilton_logs.tar.gz
 session_notes.txt
 ```
* Extract the tar:

  ```
  access.log
  ```

---

# **Clue 5 — Bletsch / RAID Analysis**

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
