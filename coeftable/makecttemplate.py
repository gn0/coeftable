import argh
import re
import operator as op
import itertools as it
import copy


def consistent_item_count(*args):
    first_item_count = None

    for iterable in it.chain(*args):
        if first_item_count is None:
            first_item_count = len(iterable)
        elif first_item_count != len(iterable):
            return False

    return True


assert consistent_item_count([[1, 2, 3]]) == True
assert consistent_item_count([[1, 2, 3], [1, 2, 3]]) == True
assert consistent_item_count([[1, 2, 3], [1, 2, 3, 4]]) == False
assert consistent_item_count([[1, 2, 3]], [[1, 2, 3]]) == True
assert consistent_item_count([[1, 2, 3]], [[1, 2, 3, 4]]) == False


def into_list_if_not_None(*args):
    return [arg for arg in args if arg is not None]


assert into_list_if_not_None(1, None, 2) == [1, 2]
assert into_list_if_not_None(None, None, None) == []


def code_for_path(path, instance_index, spec_as_coefs):
    if spec_as_coefs:
        return "@@%d::%s@@" % (instance_index, path)
    else:
        return "%%(%d::%s).3f" % (instance_index, path)


def parse_coef(code):
    m = re.match(r"^@@(\d+)::(.+)@@$", code)

    if m is None:
        return None

    return (m.group(1), m.group(2))


def is_coef(code):
    return parse_coef(code) is not None


def resolve_coef(code):
    try:
        a, b = parse_coef(code)
    except TypeError:
        return None

    return ("%%(%s::coef::%s::est).3f" % (a, b),
            "%%(%s::coef::%s::stars)s" % (a, b),
            "%%(%s::coef::%s::se).4f" % (a, b))


def is_float_format(code):
    m = re.match(r"^%\([^)]+\)[0-9]*[.][0-9]+f$", code)

    return m is not None


def assemble_panels(
        spec_defs,
        spec_as_coefs,
        var_labels,
        panel_defs,
        footer_rows,
        footer_vars,
        footer_var_labels):
    """
    Returns a list of panels, each of which is a list of
    columns, each of which is a list of cells.
    """

    panels = []
    instance_index = 0
    first_col = None

    for panel_def in panel_defs:
        if first_col is None:
            first_col = copy.deepcopy(var_labels)

            if footer_rows:
                first_col += [row[0] for row in footer_rows]

            if footer_var_labels:
                first_col += footer_var_labels

        panel_cols = [first_col]
        col_index = 0

        for spec_id in panel_def:
            instance_index += 1
            col_index += 1

            cells = [code_for_path(
                         path, instance_index, spec_as_coefs)
                     if path else ""
                     for path in spec_defs[spec_id - 1]]

            if footer_rows:
                cells += [row[col_index] for row in footer_rows]

            if footer_vars:
                cells += ["%%(%d::%s)s" % (instance_index, var)
                          for var in footer_vars]

            panel_cols.append(cells)

        panels += [panel_cols]

    return panels


def rows_from(panel):
    n_cols = len(panel)
    n_rows = len(panel[0])

    for j in xrange(n_rows):
        yield tuple(panel[i][j] for i in xrange(n_cols))


def csv_from(panels):
    raise NotImplementedError(
              "--output-as csv is not implemented yet.")


def markdown_from(panels):
    raise NotImplementedError(
              "--output-as markdown is not implemented yet.")


def latex_from(panels, without_coef_stars):
    n_cols = len(panels[0])
    n_rows = len(panels[0][0])
    n_panels = len(panels)

    #
    # Header
    #

    code = (r"\begin{tabular}{l *{%d}{c}}" % (n_cols - 1)) + "\n"
    code += r"\toprule" + "\n"

    for i in xrange(1, n_cols):
        code += " & (%d)" % i
    code += r" \\" + "\n"

    code += r"\midrule" + "\n"

    #
    # Panels
    #

    for panel_index, panel in enumerate(panels):
        if n_panels > 1:
            code += (r"& \multicolumn{%d}{c}{\em Panel %s} \\[1em]"
                     % (n_cols - 1, chr(65 + panel_index))) + "\n"

        # Body and footer
        #

        for row_index, row in enumerate(rows_from(panel)):
            # TODO Escape LaTeX special characters.

            this_line = ""
            next_line = ""

            if any(is_coef(cell) for cell in row[1:]):
                this_line += row[0]

                for cell in row[1:]:
                    if not is_coef(cell):
                        this_line += " & %s" % cell
                        next_line += " & "
                    else:
                        est, stars, se = resolve_coef(cell)

                        if without_coef_stars:
                            this_line += " & $%s$" % est
                        else:
                            this_line += " & $%s$%s" % (est, stars)
                        next_line += " & ($%s$)" % se

                code += this_line + r" \\" + "\n"
                code += next_line + r" \\[1em]" + "\n"
            else:
                this_line += row[0]

                for cell in row[1:]:
                    if is_float_format(cell):
                        this_line += " & $%s$" % cell
                    else:
                        this_line += " & %s" % cell

                code += this_line + r" \\" + "\n"

    code += r"\bottomrule" + "\n"
    code += r"\end{tabular}"

    return code


@argh.arg("--define-spec", type=str, nargs="+", required=True, action="append")
@argh.arg("--var-labels", type=str, nargs="+", required=True)
@argh.arg("--add-panel", type=int, nargs="+", action="append")
@argh.arg("--add-footer-row", type=str, nargs="+", action="append")
@argh.arg("--add-footer-var", type=str, nargs="+")
@argh.arg("--footer-var-labels", type=str, nargs="+")
@argh.arg("--output-as", type=str, required=True, choices=("csv", "markdown", "latex"))
def dispatcher(
        define_spec=None,
        spec_as_coefs=False,
        without_coef_stars=False,
        var_labels=None,
        add_panel=None,
        add_footer_row=None,
        add_footer_var=None,
        footer_var_labels=None,
        output_as=None):
    if op.xor(add_footer_var is None,
              footer_var_labels is None):
        raise argh.exceptions.CommandError(
                  "Must specify either both --add-footer-var "
                  + "and --footer-var-labels or neither.")

    if add_panel is None:
        add_panel = [[1]]

    if not consistent_item_count(
               *into_list_if_not_None(
                    define_spec,
                    var_labels)):
        raise argh.exceptions.CommandError(
                  "Number of rows implied by specifications "
                  + "and variable labels must be equal.")

    if not consistent_item_count(
               *into_list_if_not_None(
                    [[None] + p for p in add_panel],
                    add_footer_row)):
        raise argh.exceptions.CommandError(
                  "Number of columns implied by panels and "
                  + "footer rows must be equal.")

    panels = assemble_panels(
                 spec_defs=define_spec,
                 spec_as_coefs=spec_as_coefs,
                 var_labels=var_labels,
                 panel_defs=add_panel,
                 footer_rows=add_footer_row,
                 footer_vars=add_footer_var,
                 footer_var_labels=footer_var_labels)

    print panels

    # TODO
    # - Each of these views will need to be ready to resolve
    #   @@*::*@@-type coefficient shorthands.
    #
    if output_as == "csv":
        print csv_from(panels)
    elif output_as == "markdown":
        print markdown_from(panels)
    else:
        print latex_from(panels, without_coef_stars)


def main():
    argh.dispatch_command(dispatcher)


if __name__ == "__main__":
    main()
