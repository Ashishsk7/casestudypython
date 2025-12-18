import csv
import json
import matplotlib.pyplot as plt

# ---------- DECORATOR: validate ingredient inputs ----------

def validate_ingredient_input(func):
    def wrapper(self, name, quantity, price_by_store):
        if not name:
            raise ValueError("Ingredient name cannot be empty")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if not price_by_store or not isinstance(price_by_store, dict):
            raise ValueError("price_by_store must be a non-empty dictionary")
        for store, price in price_by_store.items():
            if price <= 0:
                raise ValueError(f"Price for store '{store}' must be positive")
        return func(self, name, quantity, price_by_store)
    return wrapper

# ---------- CLASS: RecipeCost ----------

class RecipeCost:
    def __init__(self, name, servings):
        self.name = name
        self.servings = servings
        self.ingredients = []   # each ingredient will be a dict

    @validate_ingredient_input
    def add_ingredient(self, name, quantity, price_by_store):
        ingredient = {
            "name": name,
            "quantity": quantity,
            "price_by_store": price_by_store   # dict: {"StoreA": 10, "StoreB": 8}
        }
        self.ingredients.append(ingredient)

    # LAMBDA for ingredient cost at a given store
    def ingredient_cost_for_store(self, ingredient, store_name):
        cost_func = lambda qty, price: qty * price  # lambda as required
        price = ingredient["price_by_store"].get(store_name)
        if price is None:
            return None
        return cost_func(ingredient["quantity"], price)

    def total_cost_at_store(self, store_name):
        costs = []
        for ing in self.ingredients:
            c = self.ingredient_cost_for_store(ing, store_name)
            if c is not None:
                costs.append(c)
        return sum(costs)

    def per_serving_cost(self, store_name):
        total = self.total_cost_at_store(store_name)
        if self.servings == 0:
            return 0
        return total / self.servings

    # Use list comprehension to find cheapest store
    def cheapest_store(self):
        if not self.ingredients:
            return None, 0

        # collect all store names from ingredients using list comprehension
        all_stores = {store for ing in self.ingredients for store in ing["price_by_store"].keys()}
        store_costs = []
        for store in all_stores:
            cost = self.total_cost_at_store(store)
            store_costs.append((store, cost))

        cheapest = min(store_costs, key=lambda x: x[1])
        return cheapest  # (store_name, cost)

# ---------- HELPER FUNCTIONS: CSV, JSON, BAR CHART ----------

def save_to_csv(recipe, filename="recipe_costs.csv"):
    fieldnames = ["ingredient", "quantity", "store", "price_per_unit", "cost"]
    with open(filename, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # write one row per ingredient per store
        for ing in recipe.ingredients:
            name = ing["name"]
            qty = ing["quantity"]
            for store, price in ing["price_by_store"].items():
                cost = qty * price
                writer.writerow({
                    "ingredient": name,
                    "quantity": qty,
                    "store": store,
                    "price_per_unit": price,
                    "cost": cost
                })

def save_summary_to_json(recipe, filename="recipe_summary.json"):
    cheapest_store_name, cheapest_cost = recipe.cheapest_store()
    summary = {
        "recipe_name": recipe.name,
        "servings": recipe.servings,
        "cheapest_store": cheapest_store_name,
        "cheapest_total_cost": cheapest_cost,
        "per_serving_cost_at_cheapest_store": recipe.per_serving_cost(cheapest_store_name)
    }
    with open(filename, "w") as f:
        json.dump(summary, f, indent=4)

def plot_ingredient_costs(recipe, store_name):
    ingredient_names = [ing["name"] for ing in recipe.ingredients]
    costs = []
    for ing in recipe.ingredients:
        c = recipe.ingredient_cost_for_store(ing, store_name)
        if c is None:
            c = 0
        costs.append(c)

    plt.bar(ingredient_names, costs, color="skyblue")
    plt.xlabel("Ingredients")
    plt.ylabel("Cost at " + store_name)
    plt.title(f"Ingredient Costs for {recipe.name} at {store_name}")
    plt.show()

# ---------- MAIN-LIKE INTERACTION (simple for Colab) ----------

def run_recipe_cost_demo():
    print("=== Recipe Ingredient Cost Analyzer ===")
    name = input("Enter recipe name: ")
    servings = int(input("Enter number of servings: "))

    recipe = RecipeCost(name, servings)

    while True:
        add_more = input("Add ingredient? (y/n): ").strip().lower()
        if add_more != "y":
            break

        ing_name = input("Ingredient name: ")
        qty = float(input("Quantity (e.g., 0.5 for 0.5 kg): "))

        price_by_store = {}
        while True:
            store_name = input("Store name (or 'done' to stop adding stores): ").strip()
            if store_name.lower() == "done":
                break
            price = float(input(f"Price per unit at {store_name}: "))
            price_by_store[store_name] = price

        try:
            recipe.add_ingredient(ing_name, qty, price_by_store)
        except ValueError as e:
            print("Error:", e)
            continue

    # If at least one ingredient was added, show results
    if recipe.ingredients:
        store, total = recipe.cheapest_store()
        print("\n=== RESULTS ===")
        print("Recipe name:", recipe.name)
        print("Servings:", recipe.servings)
        print("Cheapest store:", store)
        print("Total cost at cheapest store:", total)
        print("Cost per serving at cheapest store:", recipe.per_serving_cost(store))

        save_to_csv(recipe)
        save_summary_to_json(recipe)
        print("Data saved to recipe_costs.csv and recipe_summary.json")

        # Plot bar chart for the cheapest store
        plot_ingredient_costs(recipe, store)

    else:
        print("No ingredients added, nothing to calculate.")

# actually run the demo when cell is run
run_recipe_cost_demo()
