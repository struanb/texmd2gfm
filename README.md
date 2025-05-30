# texmd2gfm

Convert LaTeX-generated Markdown to GitHub-compatible Markdown (GFM) for better rendering of equations, references, and labels.

This script is intended to clean up and post-process Markdown files generated by Pandoc from LaTeX sources, adjusting references, math labels, and formatting so they render properly on GitHub and similar Markdown viewers.

## Features

- Converts Pandoc/LaTeX references (`\ref`, `\eqref`) into GFM-compatible hyperlinks.
- Handles labeled equations by attaching numbered tags or readable labels.
- Converts `$$...$$` math blocks into fenced code blocks with math language tag.
- Inserts HTML anchors for equations and cross-references (`<a id="..."></a>`).
- Supports flexible formatting styles for math labels, including:
  - `\tag{label}`
  - `\qquad\text{(label)}`
  - `<p align="right">(label)</p>`
- Rewrites references like `eq:xyz` with readable equation numbers (1, 2, 3, ...).
- Can simplify Pandoc-generated HTML math references to standard Markdown links.

## Usage

Convert a LaTeX file to Markdown using Pandoc, then post-process with `texmd2gfm.py`.

```bash
pandoc --from=latex --to=gfm+tex_math_dollars input.tex \
    | python3 texmd2gfm.py --label-type p > output.md
```

You can also specify an input file:

```bash
python3 texmd2gfm.py converted.md --label-type tag > cleaned.md
```

### Arguments

- `input_file`: Path to the Markdown file to transform. If omitted, reads from standard input (stdin).

### Options

- `--remove-parens`: Remove parentheses around equation references (e.g. ([eq:label]) → [eq:label]).
- `--keep-link-brackets`: Use single brackets for links ([label](#label)) instead of double brackets ([[label]](#label)).
- `--label-type TYPE`: How to render `\label{...}` in math environments. Options:
  - `tag`: Inserts `\tag{label}` directly into the LaTeX block (default). Renders beautifully in VS Code but not (yet) in GitHub.
  - `quadd:<n>`: Appends n `\qquad` spaces + `\text{(label)}` inside the math block. Renders well in GitHub.
  - `p`: Adds a right-aligned HTML paragraph above the math block: `<p align="right">(label)</p>`. Recommended for GitHub.

Example:

```bash
python3 texmd2gfm.py --label-type quadd:2 math.md
```

## Example

Given this input Markdown, obtained from `pandoc --from=latex --to=gfm+tex_math_dollars`:

```latex
Let $w$ and $f_{1}$, $f_{2}$, …,$f_{m}$ be functions that are bounded
and continuous in the interval $\left[a,b\right]$.

Let $$w=A\,U\left(x\right)+\boldsymbol{T}_{1}\left\{ U\right\} r\left(x\right).\label{eq:1000}$$

Then equation (<a href="#eq:1000" data-reference-type="ref"
data-reference="eq:1000">[eq:1000]</a>) is good to go!

```

The output, processed using `texmd2gfm.py --label-type p`, should look like:

```markdown
Let $`w`$ and $`f_{1}`$, $`f_{2}`$, …,$`f_{m}`$ be functions that are bounded
and continuous in the interval $`\left[a,b\right]`$.

Let 
<a id="1"></a>
<p align="right">(1)</p>

```math
w=A\,U\left(x\right)+\boldsymbol{T}_{1}\left\{ U\right\} r\left(x\right).
​```

Then equation ([1](#1)) is good to go!
```

And this markdown, rendered in a Github `.md` file, looks like:

Let $`w`$ and $`f_{1}`$, $`f_{2}`$, …,$`f_{m}`$ be functions that are bounded
and continuous in the interval $`\left[a,b\right]`$.

Let

<a id="1"></a>
<p align="right">(1)</p>

```math
w=A\,U\left(x\right)+\boldsymbol{T}_{1}\left\{ U\right\} r\left(x\right).
```

Then equation ([1](#1)) is good to go!

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)

## Tips

- Always run this script after converting LaTeX to Markdown with Pandoc.
- This tool is especially useful if you're putting LaTeX-derived documents on GitHub Pages, README files, or static sites.

## License

MIT License

## Author

Written by and (c) Struan Bartlett 2025, with assistance from OpenAI gpt-4o. Contributions welcome!