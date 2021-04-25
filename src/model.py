import mariadb

from error import (
    InvalidTableNameError,
    RequirementsNotMetError,
    TooManyArguments
)


def execute(connection, arguments):
    """This handles execution of all relevant arguments.

    :param connection: Database connection to run queries on
    :param arguments: Arguments passed to this program
    """
    cursor = connection.cursor()

    if arguments.show is not None:
        select_all(cursor, arguments.show)

    elif arguments.add is not None:
        # Dictionary of add functors and associated tables
        options = {
            'employee': add_employee,
            'department': add_department
        }
        if arguments.add not in options.keys():
            msg = '{} is not a valid table'.format(arguments.add)
            raise InvalidTableNameError(msg)

        # Call appropriate functor
        options[arguments.add](cursor, arguments)

    elif arguments.remove is not None:
        # Dictionary of add functors and associated tables
        options = {
            'employee': remove_employee,
            'department': remove_department
        }
        if arguments.remove not in options.keys():
            msg = '{} is not a valid table'.format(arguments.add)
            raise InvalidTableNameError(msg)

        # Call appropriate functor
        options[arguments.remove](cursor, arguments)

    elif arguments.update is not None:
        # Dictionary of add functors and associated tables
        options = {
            'employee': update_employee,
            'department': update_department
        }
        if arguments.update not in options.keys():
            msg = '{} is not a valid table'.format(arguments.add)
            raise InvalidTableNameError(msg)

        # Call appropriate functor
        options[arguments.update](cursor, arguments)

    connection.commit()  # This line saves the changes made to the database
    # Close connection once we're done with it
    cursor.close()
    connection.close()


def validate_command(arguments, required=tuple(), valid=tuple(), update=tuple()):
    """Helper function to validate arguments passed to command line fit function being called.

    :param arguments: All arguments passed to the command line.
    :param required: List of required arguments for add functionality.
    :param valid: List of valid arguments for remove functionality.
    :param update: List of valid arguments to update
    """
    arg_dict = vars(arguments)

    if len(required) > 0:
        not_met = list()
        for requirement in required:
            if arg_dict[requirement] is None:
                not_met.append(requirement)
        if len(not_met) != 0:
            msg = 'The following arguments are missing: {}'.format(not_met)
            raise RequirementsNotMetError(msg)

    if len(valid) > 0:
        total_valid = 0
        for arg in valid:
            if arg_dict[arg] is not None:
                total_valid += 1
        if total_valid != 1:
            msg = 'Pleas provide only ONE of the following arguments: {}'.format(valid)
            raise TooManyArguments(msg)

    if len(update) > 0:
        total_valid_update = 0
        for arg in update:
            if arg_dict[arg] is not None:
                total_valid_update += 1
        if total_valid_update == 0:
            msg = 'Pleas provide only ANY of the following arguments: {}'.format(update)
            raise RequirementsNotMetError(msg)


def print_cursor(cursor):
    """Helper function to print results of a cursor
    :param cursor: Cursor iterator returned by calling cursor.execute()
    """
    for row in cursor:
        print(row)


def select_all(cursor, table_name):
    """Show all tables or contents of a specific table

    Examples:
        python main.py --show tables
        python main.py --show department

    :param cursor: cursor to mariadb
    :param table_name: Name of table to display
    """

    try:
        # Show tables
        if table_name == 'tables':
            cursor.execute('SHOW tables')
        # Show contents of specific tables
        else:
            cursor.execute(f'SELECT * from {table_name}')
        print_cursor(cursor)
    except mariadb.ProgrammingError:
        msg = '{} is not a valid table name'.format(table_name)
        print(msg)


# TODO: clean this crap
def update_helper(cursor, arguments, valid_arguments, update_arguments, table_name):
    """Helper function to handle table update commands.

    :param cursor: Cursor for SQL command execution.
    :param arguments: All arguments passed to program.
    :param valid_arguments: Tuple of valid column names to run a remove statement on.
    :param update_arguments: Valid columns in table that may be updated.
    :param table_name: Table to run remove statement against.
    """
    # Make sure one of these arguments were passed to the program
    validate_command(arguments, valid=valid_arguments, update=update_arguments)
    all_args = vars(arguments)
    update_params = list()

    # Select the attribute the user decided to remove an employee by (remove by first_name, last_name, etc.)
    for arg in update_arguments:
        if all_args[arg] is not None:
            update_params.append([arg, vars(arguments)[arg]])
    print(update_params)

    search_params = dict()
    for arg in valid_arguments:
        if all_args[arg] is not None:
            search_params.update({'attribute': arg, 'value': vars(arguments)[arg]})

    for param in update_params:
        # arg[4:] will get rid of the set_ part of the string
        sql = 'UPDATE {} SET {}=? WHERE {} like ?'.format(
            table_name, param[0][4:], search_params['attribute'])
        values = (all_args[param[0]], search_params['value'])
        print(sql)
        print(values)
        cursor.execute(sql, values)
    print('Successfully updated values')


def remove_helper(cursor, arguments, valid_arguments, table_name):
    """Helper function to remove rows from tables.

    :param cursor: Cursor for SQL command execution.
    :param arguments: All arguments passed to program.
    :param valid_arguments: Tuple of valid column names to run a remove statement on.
    :param table_name: Table to run remove statement against.
    """
    # Make sure one of these arguments were passed to the program
    validate_command(arguments, valid=valid_arguments)
    all_args = vars(arguments)
    search_params = dict()

    # Select the attribute the user decided to remove an employee by (remove by first_name, last_name, etc.)
    for arg in valid_arguments:
        if all_args[arg] is not None:
            search_params.update({'attribute': arg, 'value': vars(arguments)[arg]})
    print(search_params)

    sql = 'DELETE FROM {} WHERE {} like ?'.format(table_name, search_params['attribute'])
    value = (search_params['value'],)
    cursor.execute(sql, value)
    print('Successfully removed the values')


def add_employee(cursor, arguments):
    """Add an employee to the employee table.

    Examples:
        python main.py --add employee -f Joe -l Smith -N 555-555-5555 -j 3
        python main.py --add employee --first_name Joe --last_name Smith --number 555-555-5555 --job_id 3

    :param cursor: Cursor for SQL command execution.
    :param arguments: All arguments passed to program.
    """
    # Make sure all of these arguments were passed to the program
    required_args = ('first_name', 'last_name', 'number', 'job_id')
    validate_command(arguments, required=required_args)

    sql = 'INSERT INTO employee (first_name, last_name, phone, job_id) VALUES (?, ?, ?, ?)'
    values = (
        arguments.first_name,
        arguments.last_name,
        arguments.number,
        int(arguments.job_id)
    )
    print(values)
    cursor.execute(sql, values)
    print('Successfully inserted the values')


def update_employee(cursor, arguments):
    """Update an employee.

    Examples:
        python main.py --update employee --employee_id 14 --set_fn Joe
        python main.py --update employee --first_name Bob --set_ln George

    :param cursor: Cursor for SQL command execution.
    :param arguments: All arguments passed to program.
    """
    valid_arguments = ('first_name', 'last_name', 'number', 'job_id', 'employee_id')
    update_arguments = ('set_first_name', 'set_last_name', 'set_number', 'set_job_id')
    update_helper(cursor, arguments, valid_arguments, update_arguments, 'employee')


def remove_employee(cursor, arguments):
    """Remove an employee from the employee table.

    Examples:
        python main.py --remove employee --first_name Joe
        python main.py -r employee --last_name smith
        python main.py -r employee --employee_id 7
        python main.py -r employee -e 7

    :param cursor: Cursor for SQL command execution.
    :param arguments: All arguments passed to program.
    """
    valid_args = ('first_name', 'last_name', 'employee_id')
    remove_helper(cursor, arguments, valid_args, 'employee')


def add_department(cursor, arguments):
    """Add a department to the department table.

    Examples:
        python main.py --add department --department_name NewDepartment
        python main.py -a department -D NewDepartment

    :param cursor: Cursor for SQL command execution.
    :param arguments: All arguments passed to program.
    """
    required_args = ('department_name',)
    validate_command(arguments, required=required_args)

    sql = 'INSERT INTO department (department_name) VALUES (?)'
    values = (arguments.department_name,)
    print(values)
    cursor.execute(sql, values)
    print('Successfully added values.')


def update_department(cursor, arguments):
    """Update a department.

        Examples:
            python main.py --update department --department_id 3 --set_name NewName
            python main.py -u department -i 3 --set_name NewName

        :param cursor: Cursor for SQL command execution.
        :param arguments: All arguments passed to program.
        """
    valid_arguments = ('department_name', 'department_id')
    update_arguments = ('set_department_name',)
    update_helper(cursor, arguments, valid_arguments, update_arguments, 'department')


def remove_department(cursor, arguments):
    """Remove a department from department table.

    Exampes:
        python main.py --remove department --department_name NewDepartment
        python main.py -r department -D NewDepartment

        python main.py --remove department --department_id 7
        python main.py -r department -i 7

    :param cursor: Cursor for SQL command execution.
    :param arguments: All arguments passed to program.
    """
    valid_args = ('department_id', 'department_name')
    remove_helper(cursor, arguments, valid_args, 'department')
