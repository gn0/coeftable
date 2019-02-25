import argh
import collections
import re
import operator as op
import itertools as it
import copy


Block = collections.namedtuple("Block", ("instance_index", "path"))
IndexedCell = collections.namedtuple("IndexedCell", ("instance_index", "value"))


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


def adapt_instance_index(template, instance_index):
    retval = ""
    start_pos = 0

    while 1:
        template_chunk = template[start_pos:]

        # This pattern matches the following strings:
        #
        # - %(1::N)s
        # - %(1::N)d
        # - %(1::coef::N::ci_l).3f
        # - %(1::N::mean)07.2f
        #
        # The respective group pairs that it extracts are:
        #
        # - %(, ::N)s
        # - %(, ::N)d
        # - %(, ::coef::N::ci_l).3f
        # - %(, ::N::mean)07.2f
        #
        m = re.search(
                r"(%\()1(::[^)]+\)(?:[sd]|[0-9]*[.][0-9]+f))",
                template_chunk)

        if m is None:
            retval += template_chunk
            return retval

        retval += template_chunk[:m.start()]
        retval += ("%s%d%s"
                   % (m.group(1),
                      instance_index,
                      m.group(2)))

        start_pos += m.end()


def adapt(template, template_path, instance_index, path):
    retval = ""
    start_pos = 0

    while 1:
        template_chunk = template[start_pos:]

        # This pattern matches, e.g., with template_path="N",
        # the following strings:
        #
        # - %(1::N)s
        # - %(1::N)d
        # - %(1::coef::N::ci_l).3f
        # - %(1::N::mean)07.2f
        #
        # The respective group pairs that it extracts are:
        #
        # - ::, )s
        # - ::, )d
        # - ::coef::, ::ci_l).3f
        # - ::, ::mean)07.2f
        #
        m = re.search(
                (r"%%\(1((?:::[^)]+)*::)%s((?:::[^)]+)*\)(?:[sd]|[0-9]*[.][0-9]+f))"
                 % template_path),
                template_chunk)

        if m is None:
            retval += template_chunk
            return retval

        retval += template_chunk[:m.start()]
        retval += ("%%(%d%s%s%s"
                   % (instance_index,
                      m.group(1),
                      path,
                      m.group(2)))

        start_pos += m.end()


def assemble_panels(
        spec_defs,
        var_labels,
        panel_defs,
        footer_rows,
        footer_cells,
        footer_cell_labels):
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

            if footer_cell_labels:
                first_col += footer_cell_labels

        panel_cols = [first_col]
        col_index = 0

        for spec_id in panel_def:
            instance_index += 1
            col_index += 1

            cells = [Block(instance_index=instance_index,
                           path=path)
                     if path else ""
                     for path in spec_defs[spec_id - 1]]

            if footer_rows:
                cells += [row[col_index] for row in footer_rows]

            if footer_cells:
                cells += [IndexedCell(instance_index=instance_index,
                                      value=cell)
                          for cell in footer_cells]

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


def latex_from(panels, block_template, template_path, spec_as_coefs, without_coef_stars):
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
            if panel_index > 0:
                code += r"\midrule" + "\n"

            code += (r"& \multicolumn{%d}{c}{\em Panel %s} \\[1em]"
                     % (n_cols - 1, chr(65 + panel_index))) + "\n"

        # Body and footer
        #

        for row_index, row in enumerate(rows_from(panel)):
            # TODO Escape LaTeX special characters.

            this_line = ""

            if spec_as_coefs or len(block_template) == 2:
                next_line = ""

            if any(isinstance(cell, Block) for cell in row[1:]):
                this_line += row[0]

                for cell in row[1:]:
                    if not cell:
                        this_line += " & "

                        if spec_as_coefs or len(block_template) == 2:
                            next_line += " & "
                    elif spec_as_coefs:
                        this_line += (" & $%%(%d::coef::%s::est).3f$"
                                      % (cell.instance_index,
                                         cell.path))
                        if not without_coef_stars:
                            this_line += ("%%(%d::coef::%s::stars)s"
                                          % (cell.instance_index,
                                             cell.path))

                        next_line += (" & ($%%(%d::coef::%s::se).4f$)"
                                      % (cell.instance_index,
                                         cell.path))
                    else:
                        this_line += " & "
                        this_line += adapt(
                                         block_template[0],
                                         template_path,
                                         cell.instance_index,
                                         cell.path)

                        if len(block_template) == 2:
                            next_line += " & "
                            next_line += adapt(
                                             block_template[1],
                                             template_path,
                                             cell.instance_index,
                                             cell.path)

                code += this_line + r" \\" + "\n"

                if spec_as_coefs or len(block_template) == 2:
                    code += next_line + r" \\[1em]" + "\n"
            else:
                this_line += row[0]

                for cell in row[1:]:
                    this_line += " & "

                    if isinstance(cell, IndexedCell):
                        this_line += adapt_instance_index(
                                         cell.value,
                                         cell.instance_index)
                    else:
                        this_line += cell

                code += this_line + r" \\" + "\n"

    code += r"\bottomrule" + "\n"
    code += r"\end{tabular}"

    return code


@argh.arg("--define-spec", type=str, nargs="+", required=True, action="append")
@argh.arg("--var-labels", type=str, nargs="+", required=True)
@argh.arg("--block-template", type=str, nargs="+")
@argh.arg("--add-panel", type=int, nargs="+", action="append")
@argh.arg("--add-footer-row", type=str, nargs="+", action="append")
@argh.arg("--add-footer-cell", type=str, nargs="+")
@argh.arg("--footer-cell-labels", type=str, nargs="+")
@argh.arg("--output-as", type=str, required=True, choices=("csv", "markdown", "latex"))
def dispatcher(
        define_spec=None,
        var_labels=None,
        block_template=None,
        spec_as_coefs=False,
        without_coef_stars=False,
        add_panel=None,
        add_footer_row=None,
        add_footer_cell=None,
        footer_cell_labels=None,
        output_as=None):
    if op.xor(block_template is None,
              spec_as_coefs):
        raise argh.exceptions.CommandError(
                  "Must specify either --block-template or "
                  + "--spec-as-coefs (and not both).")
    elif op.xor(add_footer_cell is None,
                footer_cell_labels is None):
        raise argh.exceptions.CommandError(
                  "Must specify either both --add-footer-var "
                  + "and --footer-var-labels or neither.")
    elif block_template is not None and len(block_template) > 2:
        raise NotImplementedError(
                  "--block-template can't have more than two "
                  + "arguments.")

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

    if block_template:
        template_path = define_spec[0][0]
    else:
        template_path = None

    panels = assemble_panels(
                 spec_defs=define_spec,
                 var_labels=var_labels,
                 panel_defs=add_panel,
                 footer_rows=add_footer_row,
                 footer_cells=add_footer_cell,
                 footer_cell_labels=footer_cell_labels)

    if output_as == "csv":
        print csv_from(panels)
    elif output_as == "markdown":
        print markdown_from(panels)
    else:
        print latex_from(
                  panels,
                  block_template,
                  template_path,
                  spec_as_coefs,
                  without_coef_stars)


def main():
    argh.dispatch_command(dispatcher)


if __name__ == "__main__":
    main()
