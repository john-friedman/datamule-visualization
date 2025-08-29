# secbrowser [NOT READY FOR USE]

A simple interface to interact with SEC filings. Part of [datamule](https://github.com/john-friedman/datamule-python).

## Why this was made

- I needed a good visual interface to improve doc2dict
- I needed a good visual interface to explore nlp
- I wanted to stress test datamule's functionality. This is an opportunity to improve architecture / add useful stuff.

## Why it may be useful for you
- Easier UI
- You like visualizations

## Features TBD
- Document page with text, data, tables, nlp, etc
- Adding CSS
- Adding custom templates to change style
- add maximize window to document tabs
- chatbot integration


## Arch
- we will use iframes and new windows then switch

for text - probably setup within iframe if possible, 
little div or something with checkboxes as well as use dictionary (should label here reminder to label in code)
also add text sim

we can copy this for data
then it's just a tweak for highlight and sim
think through generalization
oh wait. dont do this in the iframe for now
just have stuff at top

Tags:
persons, tickers, etc with highlight default color and color picker

Similarity:
with choose type -> that creates colors for types since we dont predefine types

OKAY SO
we will just go with new windows for now
later -> port within iframe


## Improvements to be made to datamule
- Change how submissions load from list based to hash. O(1).
- Change how to select type and cik.