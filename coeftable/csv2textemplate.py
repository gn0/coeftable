import sys
import csv
import re


def parse_coef(v):
    m = re.match(r"^@@(\d+)::(.+)@@$", v)

    if m is None:
        return None

    return (m.group(1), m.group(2))


def is_coef(v):
    return parse_coef(v) is not None


def coef_from(v):
    a, b = parse_coef(v)

    return ("$%%(%s::coef::%s::est).3f$%%(%s::coef::%s::stars)s"
            % (a, b, a, b))


def se_from(v):
    a, b = parse_coef(v)

    return "($%%(%s::coef::%s::se).4f$)" % (a, b)


def parse_verbatim(v):
    m = re.match(r"^#: *(.+)$", v)

    if m is None:
        return None

    return m.group(1)


def is_verbatim(row):
    return parse_verbatim(row[0]) is not None


def template_to_tex(template):
    lines = []

    for row in template:
        if row[0] == "#:":
            lines.append(row[1])
        else:
            content = " & ".join(v.replace("&", "\\&")
                                 for v in row[1:])

            if re.search(r"\\(\[\d+[empt]+\])?$", content):
                lines.append(content)
            else:
                end = r"\\" if row[0] == "normal" else r"\\[1em]"
                lines.append(
                    "%s %s" % (content, end))

    return "\n".join(lines)


def main():
    code = tuple(csv.reader(sys.stdin))
    template = list()

    for row in code:
        if is_verbatim(row):
            template.append(
                ("#:", parse_verbatim(row[0])))
        else:
            template.append(
                ("normal",)
                + tuple(coef_from(v) if is_coef(v) else v
                        for v in row))

            if any(is_coef(v) for v in row):
                template.append(
                    ("padded",)
                    + tuple(se_from(v) if is_coef(v) else ""
                            for v in row))

    print template_to_tex(template)


if __name__ == "__main__":
    main()
