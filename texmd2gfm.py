import sys
import re
import argparse

from collections import defaultdict

# This script processes LaTeX-generated Markdown content to convert it into a GitHub-compatible format.
# It handles references, equations, and LaTeX math blocks, converting them to Markdown links and fenced code blocks.
# It also supports custom label rendering styles.
#
# Usage:
# pandoc --from=latex --to=gfm+tex_math_dollars <maths.tex | python3 convert_latex_to_markdown6g.py --label-type p

def generate_equation_number_mapping(output: str) -> dict:
    """
    Map equation labels to sequential numbers (1, 2, 3, ...).
    """
    equation_map = {}
    n = 1
    for line in output.splitlines():
        m = re.match(r'^\s*<a\s+id="(eq:[^"]+)"></a>', line)
        if m:
            label = m.group(1)
            if label not in equation_map:
                equation_map[label] = str(n)
                n += 1
    return equation_map

def substitute_equation_numbers(equation_map: dict, output: str) -> str:
    """
    Replace all occurrences of eq:... in references with the renumbered values
    from the equation_map.

    This includes adjusting:
    - [eq:label](#eq:label) or [[eq:label]](#eq:label)
    - Plain inline references like eq:label

    Args:
        equation_map: dict mapping from label ("eq:label") to new number ("1.1", "2.3", etc.)
        output: processed Markdown text

    Returns:
        Updated output with substituted equation numbers in references.
    """
    # Replace Markdown links like [eq:label](#eq:label)
    def replace_linked_labels(match: re.Match) -> str:
        label_inner = match.group(1)
        ref_label = match.group(2)  # label in the anchor
        new_number = equation_map.get(ref_label)
        if not new_number:
            return match.group(0)  # No change
        return f"[{new_number}](#{ref_label})"

    # Replace [[eq:label]](#eq:label)
    def replace_double_bracket_links(match: re.Match) -> str:
        label_inner = match.group(1)
        ref_label = match.group(2)
        new_number = equation_map.get(ref_label)
        if not new_number:
            return match.group(0)
        return f"[[{new_number}]](#{ref_label})"

    # Replace standalone inline eq:label
    def replace_inline_label(match: re.Match) -> str:
        full_label = match.group(0)
        new_number = equation_map.get(full_label)
        return new_number if new_number else full_label

    # Replace [eq:label](#eq:label)
    output = re.sub(r'\[eq:([^\]]+)\]\(#(eq:[^)]+)\)', replace_linked_labels, output)

    # Replace [[eq:label]](#eq:label)
    output = re.sub(r'\[\[eq:([^\]]+)\]\]\(#(eq:[^)]+)\)', replace_double_bracket_links, output)

    # Replace standalone eq:label (word-boundary safe)
    output = re.sub(r'\beq:[A-Za-z0-9_.-]+\b', replace_inline_label, output)

    return output

def simplify_pandoc_html_references(text: str, remove_parens: bool, keep_link_brackets: bool) -> str:
    """
    Convert Pandoc-style HTML anchor references like:
        (<a href="#eq:1010" data-reference-type="ref" data-reference="eq:1010">[eq:1010]</a>)
    Into simplified Markdown-style links:
        [[eq:1010]](#eq:1010), [eq:1010](#eq:1010), or eq:1010(#eq:1010)

    Options:
        remove_parens: If True, omit surrounding parentheses
        keep_link_brackets: If False, use single brackets [label](#label) instead of [[label]](#label)
    """
    def replacement(match: re.Match) -> str:
        label = match.group(1)
        # Inner text is ignored in favor of href-based label
        if keep_link_brackets:
            display_text = f'[[{label}]]'
        else:
            display_text = f'[{label}]'

        markdown_link = f'{display_text}(#{label})'
        return markdown_link if remove_parens else f'({markdown_link})'

    pattern = re.compile(
        r'\(?<a\s+href="#([^"]+)"\s+[^>]*>\s*\[[^\]]+\]\s*</a>\)?',
        re.IGNORECASE
    )
    return pattern.sub(replacement, text)

def process_latex_labeled_math(
    md_input: str,
    remove_parens: bool,
    keep_link_brackets: bool,
    label_type: str = "tag",
    quadd_count: int = 0,
) -> str:
    """
    Process LaTeX-derived Markdown content:
    - Converts \ref, \eqref, and Pandoc HTML anchors to Markdown links
    - Converts $$...$$ math blocks to fenced code blocks
    - Replaces \label{...} with specified formatting style
    - Adds <a id="..."></a> anchors for reference links

    Args:
        md_input: string containing the Markdown content
        remove_parens: whether to strip parentheses from refs
        keep_link_brackets: whether to convert [[label]] to [label]
        label_type: "tag", "quadd", or "p"
        quadd_count: number of \qquad if label_type is "quadd"
    """
    text = md_input

    # Convert \ref and \eqref to Markdown-style anchor links
    text = re.sub(r'\\(?:eq)?ref\{([^}]+)\}', r'[\1](#\1)', text)

    # Convert Pandoc-style HTML anchors (implementation assumed)
    text = simplify_pandoc_html_references(text, remove_parens, keep_link_brackets)

    def replace_block_math(match: re.Match) -> str:
        content = match.group(1).strip()

        # Extract and remove \label from math
        label_match = re.search(r'\\label\{([^}]+)\}', content)
        label = label_match.group(1) if label_match else None
        content = re.sub(r'\\label\{[^}]+\}', '', content).strip()

        # Prepare LaTeX or HTML injection based on label_type
        inject_line = None
        html_label_above = None

        if label:
            if label_type == "tag":
                inject_line = f"\\tag{{{label}}}"
            elif label_type == "quadd":
                inject_line = ('\\qquad' * quadd_count) + f"\\text{{({label})}}"
            elif label_type == "p":
                html_label_above = f'<p align="right">({label})</p>' + "\n"

        # Inject label into LaTeX math (line before \end{...})
        if inject_line:
            lines = content.splitlines()
            inserted = False
            for i in reversed(range(len(lines))):
                if '\\end{' in lines[i]:
                    lines.insert(i, inject_line)
                    inserted = True
                    break
            if not inserted:
                lines.append(inject_line)
            content = '\n'.join(lines)

        # Build block
        result = []
        result.append('')
        if label:
            result.append(f'<a id="{label}"></a>')
        if html_label_above:
            result.append(html_label_above)
        result.append('```math')
        result.append(content)
        result.append('```')
        result.append('')
        return '\n'.join(result)

    # Replace all $$...$$ blocks
    math_pattern = re.compile(r'\$\$\s*([\s\S]*?)\s*\$\$', re.MULTILINE)
    text = math_pattern.sub(replace_block_math, text)

    def replace_dollar_delimited_math(match: re.Match) -> str:
        content = match.group(1)
        return f"$`{content}`$"

    # Replace all $...$ blocks
    math_pattern = re.compile(r'\$([\s\S\$]*?)\$', re.MULTILINE)
    text = math_pattern.sub(replace_dollar_delimited_math, text)

    return text

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert LaTeX-generated Markdown to GitHub-compatible Markdown.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input Markdown (.md) file generated by: pandoc --from=latex --to=gfm+tex_math_dollars.\n"
             "If not provided, input is read from standard input."
    )
    
    parser.add_argument(
        "--remove-parens", action="store_true",
        help="Remove parentheses around citation links"
    )
    parser.add_argument(
        "--keep-link-brackets", action="store_true",
        help="Use [label](#label) instead of [[label]](#label) in references"
    )
    parser.add_argument(
        "--label-type", type=str, default="tag",
        help=(
            'Customize how \\label{...} is rendered:\n'
            "  - tag (default): inserts \\tag{...} inside math\n"
            "  - quadd:<n>: inserts <n> \\qquad followed by \\text{label} inside math\n"
            "  - p: inserts <p align=\"right\">(label)</p> above the math block (for Github Markdown compatibility)"
        )
    )
    return parser.parse_args()

def main():
    args = parse_args()

    if args.input_file:
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                md_input = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.input_file}' not found.", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        md_input = sys.stdin.read()

    # Parse and validate --label-type
    label_type = "tag"
    quadd_count = 0

    if args.label_type.startswith("quadd:"):
        try:
            quadd_count = int(args.label_type.split(":", 1)[1])
            if quadd_count <= 0:
                raise ValueError
            label_type = "quadd"
        except ValueError:
            print("Error: --label-type quadd:<n> requires a positive integer n.", file=sys.stderr)
            sys.exit(1)
    elif args.label_type == "p":
        label_type = "p"
    elif args.label_type == "tag":
        label_type = "tag"
    else:
        print(f"Error: Unsupported --label-type '{args.label_type}'.", file=sys.stderr)
        sys.exit(1)

    output = process_latex_labeled_math(
        md_input,
        remove_parens=args.remove_parens,
        keep_link_brackets=args.keep_link_brackets,
        label_type=label_type,
        quadd_count=quadd_count
    )

    # Assume these helper functions exist
    equation_dict = generate_equation_number_mapping(output)
    final_output = substitute_equation_numbers(equation_dict, output)

    sys.stdout.write(final_output)

if __name__ == "__main__":
    main()
