import utility

menu = utility.load_menu("input/menu_15items.txt")
utility.load_associations(menu, "input/associations_15items.txt")
utility.load_w2v_associations(menu)