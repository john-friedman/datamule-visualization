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
- Document page data with nlp
- Adding CSS
- Adding custom templates to change style
- chatbot integration
- hide buttons that are not relevant to certain filings.

## Architecture
- Currently features open in new windows. Will likely change to using iframes.

For NLP with data
-> same thing but with dict


## Improvements to be made to datamule
- Change how submissions load from list based to hash. O(1).
- Change how to select type and cik.
- make document.text tables nicer
- make tables failsoft.
- fix how sentiment dictionaries are accessed. right now it needs the dict, but doesnt specify it when called.