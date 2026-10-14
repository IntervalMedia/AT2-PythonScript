# Python Coding Standards

## Naming

### Single-Character Variable Names

Do not use lowercase `l`, uppercase `O`, or uppercase `I`. These characters can be easily confused with numbers in some fonts. You can use an underscore (`_`) as a single-character variable name.

### Names to Avoid

- Avoid using reserved words for user-defined names.

### Package and Module Names

- Use lowercase and short names where possible.
- Underscores can be used when needed for clarity, but they are discouraged.

### Method (Function) and Variable Names

| Symbol | Naming convention | Example |
| --- | --- | --- |
| Variable | camelCase | `computerName` |
| Method | camelCase | `readLine()` |
| Parameter | camelCase | `userInput` |
| Acronyms | CapitalCase | `HTTPServerError` |

## Program Layout

### Indentation

Python uses indentation to denote a block of code. Use four spaces instead of tabs.

### Blank Lines

Use:

- Blank lines to separate groups of related functions.
- Blank lines between multiple related one-liners; they can also be omitted.
- Blank lines in functions to denote logical sections.

## Comments

Comments help make code more readable, especially when multiple programmers collaborate on maintaining it. Good practices for comments include:

- Update comments as soon as the code is updated.
- Write comments in full sentences, including capitalisation and punctuation.
- Block comments may include multiple sentences.
- Comments must be clear and unambiguous.
- Use block comments and avoid inline comments.

### Block Comments

Use block comments to clearly describe a block's purpose and operational details. Comments are preceded by the `#` symbol and a single space. Multiline comments follow the same style.

### Inline Comments

The use of inline comments is discouraged in Python for readability. However, if an inline comment adds value to the code, it can be included. Inline comments follow the same style as block comments.

## String Quotes

Single and double quotation marks have the same meaning and functionality in Python. For consistency, select one style and use it throughout the code.

## White Space in Statements

- Use a space after a comma.
- Add spaces around operators, for example: `a + b - c = d`.

