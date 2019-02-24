import argh
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


def code_for_path(path, instance_index, without_stderr):
    if without_stderr:
        return "%%(%d::%s).3f" % (instance_index, path)
    else:
        return "@@%d::%s@@" % (instance_index, path)


def assemble_panels(
        spec_defs,
        without_stderr,
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
                         path, instance_index, without_stderr)
                     for path in spec_defs[spec_id - 1]]

            if footer_rows:
                cells += [row[col_index] for row in footer_rows]

            if footer_vars:
                cells += ["%%(%d::%s)s" % (instance_index, var)
                          for var in footer_vars]

            panel_cols.append(cells)

        panels += [panel_cols]

    return panels


@argh.arg("--define-spec", type=str, nargs="+", action="append")
@argh.arg("--define-spec-without-stderr", type=str, nargs="+", action="append")
@argh.arg("--var-labels", type=str, nargs="+", required=True)
@argh.arg("--add-panel", type=int, nargs="+", action="append")
@argh.arg("--add-footer-row", type=str, nargs="+", action="append")
@argh.arg("--add-footer-var", type=str, nargs="+")
@argh.arg("--footer-var-labels", type=str, nargs="+")
@argh.arg("--output-as", type=str, required=True, choices=("csv", "markdown", "latex"))
def dispatcher(
        define_spec=None,
        define_spec_without_stderr=None,
        var_labels=None,
        add_panel=None,
        add_footer_row=None,
        add_footer_var=None,
        footer_var_labels=None,
        output_as=None):
    if not op.xor(define_spec is None,
                  define_spec_without_stderr is None):
        raise argh.exceptions.CommandError(
                  "Must specify either --define-spec "
                  + "or --define-spec-without-stderr "
                  + "(and not both).")
    elif op.xor(add_footer_var is None,
                footer_var_labels is None):
        raise argh.exceptions.CommandError(
                  "Must specify either both --add-footer-var "
                  + "and --footer-var-labels or neither.")

    if add_panel is None:
        add_panel = [[1]]

    if not consistent_item_count(
               *into_list_if_not_None(
                    define_spec,
                    define_spec_without_stderr,
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

    spec_defs = define_spec or define_spec_without_stderr

    panels = assemble_panels(
                 spec_defs=define_spec or define_spec_without_stderr,
                 without_stderr=define_spec_without_stderr is not None,
                 var_labels=var_labels,
                 panel_defs=add_panel,
                 footer_rows=add_footer_row,
                 footer_vars=add_footer_var,
                 footer_var_labels=footer_var_labels)

    print panels

    if output_as == "csv":
        raise NotImplementedError(
                  "--output-as csv is not implemented yet.")
    elif output_as == "markdown":
        raise NotImplementedError(
                  "--output-as markdown is not implemented yet.")
    else:
        raise NotImplementedError(
                  "--output-as latex is not implemented yet.")


def main():
    argh.dispatch_command(dispatcher)


if __name__ == "__main__":
    main()
