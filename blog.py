import sqlite3 as sq
import argparse


def first_tables(db_name):
    data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
            "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
            "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}
    conn = sq.connect(db_name)
    cursor_name = conn.cursor()
    cursor_name.execute('''CREATE TABLE IF NOT EXISTS meals(
        meal_id INT PRIMARY KEY,
        meal_name VARCHAR(50) NOT NULL UNIQUE);''')
    cursor_name.execute('''CREATE TABLE IF NOT EXISTS ingredients(
        ingredient_id INT PRIMARY KEY,
        ingredient_name VARCHAR(50) NOT NULL UNIQUE);''')
    cursor_name.execute('''CREATE TABLE IF NOT EXISTS measures(
        measure_id INT PRIMARY KEY,
        measure_name VARCHAR(50) UNIQUE);''')
    conn.commit()

    for key in data:
        sqlreq = f'INSERT INTO {key} VALUES '
        n = 1
        values = data[key]
        for val in values:
            val_str = f'({n}, "{val}")' + (', ' if n < len(values) else ';')
            sqlreq = sqlreq + val_str
            n += 1
        try:
            cursor_name.execute(sqlreq)
        except sq.IntegrityError:
            break
        else:
            conn.commit()
    conn.close()


def recipes_table(db_name):
    conn = sq.connect(db_name)
    cursor_name = conn.cursor()
    cursor_name.execute('''CREATE TABLE IF NOT EXISTS recipes (
        recipe_id INTEGER PRIMARY KEY,
        recipe_name VARCHAR(50) NOT NULL,
        recipe_description TEXT);''')
    conn.commit()
    conn.close()


def new_recipe(db_name):
    print('Pass the empty recipe name to exit.')
    r_name = input('Recipe name: ')
    if r_name != '':
        r_descr = input('Recipe description: ')
        conn = sq.connect(db_name)
        cursor_name = conn.cursor()
        rec_id = cursor_name.execute(f'''INSERT INTO recipes (recipe_name, recipe_description) 
    VALUES ("{r_name}", "{r_descr}");''').lastrowid
        conn.commit()
        result = cursor_name.execute('SELECT * FROM meals')
        all_rows = result.fetchall()
        f_str = ''
        for i in all_rows:
            i = [str(x) for x in i]
            f_str = f'{f_str} {") ".join(i)}'
        print(f_str)
        dishes = input('When dish can be served: ').split(' ')
        for i in dishes:
            cursor_name.execute(f'INSERT INTO serve (recipe_id, meal_id) VALUES ({rec_id}, {i});')
            conn.commit()
        add_ingredients(conn, cursor_name, rec_id)
        conn.close()
        new_recipe(db_name)


def add_ingredients(conn, cursor_name, rec_id):
    u_ingredients = input('Input quantity of ingredient <press enter to stop>: ').split(' ')
    if u_ingredients:
        if len(u_ingredients) == 2:
            measures = cursor_name.execute(f'SELECT measure_id FROM measures WHERE measure_name LIKE ""').fetchall()
            ingredients = cursor_name.execute(f'''SELECT ingredient_id FROM ingredients 
WHERE ingredient_name LIKE "%{u_ingredients[1]}%"''').fetchall()
            if len(ingredients) != 1:
                print('The ingredient is not conclusive!')
                add_ingredients(conn, cursor_name, rec_id)
            else:
                cursor_name.execute(f'''INSERT INTO quantity (quantity, ingredient_id, measure_id, recipe_id) 
            VALUES ({u_ingredients[0]}, {ingredients[0][0]}, {measures[0][0]},  {rec_id})''')
                conn.commit()
                add_ingredients(conn, cursor_name, rec_id)
        elif len(u_ingredients) == 3:
            measures = cursor_name.execute(f'''SELECT measure_id FROM measures 
WHERE measure_name LIKE "{u_ingredients[1]}%"''').fetchall()
            if len(measures) != 1:
                print('The measure is not conclusive!')
                add_ingredients(conn, cursor_name, rec_id)
            else:
                ingredients = cursor_name.execute(f'''SELECT ingredient_id FROM ingredients 
WHERE ingredient_name LIKE "%{u_ingredients[2]}%"''').fetchall()
                if len(ingredients) != 1:
                    print('The ingredient is not conclusive!')
                    add_ingredients(conn, cursor_name, rec_id)
                else:
                    cursor_name.execute(f'''INSERT INTO quantity (quantity, ingredient_id, measure_id, recipe_id)
                    VALUES ({u_ingredients[0]}, {ingredients[0][0]}, {measures[0][0]},  {rec_id})''')
                    conn.commit()
                    add_ingredients(conn, cursor_name, rec_id)


def serve_table(db_name):
    conn = sq.connect(db_name)
    cursor_name = conn.cursor()
    cursor_name.execute('PRAGMA foreign_keys = ON;')
    cursor_name.execute('''CREATE TABLE IF NOT EXISTS serve (
        serve_id INTEGER PRIMARY KEY,
        recipe_id INTEGER  NOT NULL,
        meal_id INTEGER  NOT NULL,
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(meal_id) REFERENCES meals(meal_id)
        );''')
    conn.commit()
    conn.close()


def quantity_table(db_name):
    conn = sq.connect(db_name)
    cursor_name = conn.cursor()
    cursor_name.execute('PRAGMA foreign_keys = ON;')
    cursor_name.execute('''CREATE TABLE IF NOT EXISTS quantity (
        quantity_id INTEGER PRIMARY KEY,
        measure_id INTEGER NOT NULL,
        ingredient_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        recipe_id INTEGER  NOT NULL,
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY(measure_id) REFERENCES measures(measure_id)
        );''')
    conn.commit()
    conn.close()


def check_args(db_name, u_ingredients, u_meals):
    sql_list = []
    for ingredient in u_ingredients:
        sql_list.append(f'''SELECT recipe_id FROM quantity q
    JOIN ingredients i ON i.ingredient_id = q.ingredient_id
    WHERE ingredient_name ="{ingredient}"''')
    sql_list.append(f"""SELECT recipe_id FROM serve s
    JOIN meals m ON m.meal_id = s.meal_id
    WHERE meal_name {'IN' + str(tuple([x for x in u_meals])) if len(u_meals) != 1 else '= "' + u_meals[0] + '"'}""")
    sql_query = "\nINTERSECT\n".join(sql_list)
    sql_query = f'''SELECT recipe_name FROM recipes
WHERE recipe_id IN ({sql_query})'''
    print(sql_query)
    conn = sq.connect(db_name)
    cursor_name = conn.cursor()
    check_args_indb = cursor_name.execute(sql_query).fetchall()
    if check_args_indb:
        recipes = [x[0] for x in check_args_indb]
        print(f'Recipes selected for you: {", ".join(recipes)}')
    else:
        print('There are no such recipes in the database.')


parser = argparse.ArgumentParser()
parser.add_argument("database")
parser.add_argument("--ingredients")
parser.add_argument("--meals")
args = parser.parse_args()
first_tables(args.database)
recipes_table(args.database)
serve_table(args.database)
quantity_table(args.database)

if args.ingredients is None or args.meals is None:
    new_recipe(args.database)
else:
    user_ingredients = args.ingredients.split(',')
    user_meals = args.meals.split(',')
    check_args(args.database, user_ingredients, user_meals)
