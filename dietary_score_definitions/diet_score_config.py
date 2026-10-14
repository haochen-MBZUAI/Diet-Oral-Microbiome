DASH_CONFIG = {
    "total_fat_pct_energy": {
        "nutrient": "total_fat_pct_energy",
        "direction": "lower",
        "target": 27.0,
        "intermediate": 32.0
    },
    "protein_pct_energy": {
        "nutrient": "protein_pct_energy",
        "direction": "higher",
        "target": 18.0,
        "intermediate": 16.5
    },
    "fiber_g_per_1000kcal": {
        "nutrient": "fiber_g",
        "direction": "higher",
        "target": 14.8,
        "intermediate": 9.5
    },
    "sodium_mg_per_1000kcal": {
        "nutrient": "sodium_mg",
        "direction": "lower",
        "target": 1143.0,
        "intermediate": 1286.0
    }
}

EAT_LANCET_CONFIG = {
    "Vegetables": {
        "categories": ["Vegetables"],
        "unit": "g_per_day",
        "score_3": [300, None],
        "score_2": [200, 300],
        "score_1": [100, 200],
        "score_0": [None, 100]
    },
    "Fruits": {
        "categories": ["Fruits"],
        "unit": "g_per_day",
        "score_3": [200, None],
        "score_2": [100, 200],
        "score_1": [50, 100],
        "score_0": [None, 50]
    },
    "Unsaturated oils": {
        "categories": ["Med Oil and fats"],
        "unit": "g_per_day",
        "score_3": [40, None],
        "score_2": [20, 40],
        "score_1": [10, 20],
        "score_0": [None, 10]
    },
    "Legumes": {
        "categories": ["Pulses and products"],
        "unit": "g_per_day",
        "score_3": [75, None],
        "score_2": [37.5, 75],
        "score_1": [18.75, 37.5],
        "score_0": [None, 18.75]
    },
    "Nuts": {
        "categories": ["Nuts, seeds, and products"],
        "unit": "g_per_day",
        "score_3": [50, None],
        "score_2": [25, 50],
        "score_1": [12.5, 25],
        "score_0": [None, 12.5]
    },
    "Whole grains": {
        "categories": ["Pasta, Grains and Side dishes_wholewheat", "Bread_wholewheat", "Cereals_wholewheat"],
        "unit": "g_per_day",
        "score_3": [232, None],
        "score_2": [116, 232],
        "score_1": [58, 116],
        "score_0": [None, 58]
    },
    "Fish": {
        "categories": ["Fish and seafood"],
        "unit": "g_per_day",
        "score_3": [28, None],
        "score_2": [14, 28],
        "score_1": [7, 14],
        "score_0": [None, 7]
    },
    "Beef and lamb": {
        "categories": ["Beef, veal, lamb, and other meat products"],
        "unit": "g_per_day",
        "score_3": [None, 7],
        "score_2": [7, 14],
        "score_1": [14, 28],
        "score_0": [28, None]
    },
    "Pork": {
        "categories": ["Non kosher foods"],
        "unit": "g_per_day",
        "score_3": [None, 7],
        "score_2": [7, 14],
        "score_1": [14, 28],
        "score_0": [28, None]
    },
    "Poultry": {
        "categories": ["Poultry and its products"],
        "unit": "g_per_day",
        "score_3": [None, 29],
        "score_2": [29, 58],
        "score_1": [58, 116],
        "score_0": [116, None]
    },
    "Eggs": {
        "categories": ["Eggs and their products"],
        "unit": "g_per_day",
        "score_3": [None, 13],
        "score_2": [13, 25],
        "score_1": [25, 50],
        "score_0": [50, None]
    },
    "Dairy": {
        "categories": ["milk, cream cheese and yogurts"],
        "unit": "g_per_day",
        "score_3": [None, 250],
        "score_2": [250, 500],
        "score_1": [500, 1000],
        "score_0": [1000, None]
    },
    "Tubers": {
        "categories": ["Tubers"],
        "unit": "g_per_day",
        "score_3": [None, 50],
        "score_2": [50, 100],
        "score_1": [100, 200],
        "score_0": [200, None]
    },
    "Added sugar": {
        "categories": ["NOVA_3_4_sugar"],
        "unit": "g_per_day",
        "score_3": [None, 31],
        "score_2": [31, 62],
        "score_1": [62, 124],
        "score_0": [124, None]
    }
}

IMEDAS_CONFIG = {
    "I_MED_1_olive_oil_main_source": {
        "type": "difference_positive",
        "positive_categories": ["Med Oil and fats"],
        "negative_categories": ["Oils and fats"],
        "threshold": 0,
        "points": 1
    },
    "I_MED_2_poultry_vs_red_meat": {
        "type": "difference_positive",
        "positive_categories": ["Poultry and its products"],
        "negative_categories": ["Beef, veal, lamb, and other meat products"],
        "threshold": 0,
        "points": 1
    },
    "I_MED_3_vegetables": {
        "type": "min_kcal_per_day",
        "categories": ["Vegetables"],
        "threshold_kcal": 60,
        "points": 1
    },
    "I_MED_4_fruits": {
        "type": "min_kcal_per_day",
        "categories": ["Fruits"],
        "threshold_kcal": 210,
        "points": 1
    },
    "I_MED_5_margarine_butter": {
        "type": "max_kcal_per_day",
        "categories": ["Oils and fats"],
        "threshold_kcal": 80,
        "points": 1
    },
    "I_MED_6_sweetened_drinks": {
        "type": "max_kcal_per_day",
        "categories": ["fruit juices and soft drinks"],
        "threshold_kcal": 50,
        "points": 1
    },
    "I_MED_7_whole_grains": {
        "type": "min_kcal_per_day",
        "categories": ["Bread_wholewheat", "Pasta, Grains and Side dishes_wholewheat", "Cereals_wholewheat"],
        "threshold_kcal": 210,
        "points": 1
    },
    "I_MED_8_dairy": {
        "type": "min_kcal_per_day",
        "categories": ["milk, cream cheese and yogurts"],
        "threshold_kcal": 180,
        "points": 1
    },
    "I_MED_9_red_meat": {
        "type": "max_kcal_per_day",
        "categories": ["Beef, veal, lamb, and other meat products"],
        "threshold_kcal": 220,
        "points": 1
    },
    "I_MED_10_alcoholic_drinks": {
        "type": "min_kcal_per_day",
        "categories": ["Alcoholic Drinks"],
        "threshold_kcal": 125,
        "points": 1
    },
    "I_MED_11_legumes": {
        "type": "min_kcal_per_day",
        "categories": ["Pulses and products"],
        "threshold_kcal": 72.85,
        "points": 1
    },
    "I_MED_12_fish": {
        "type": "min_kcal_per_day",
        "categories": ["Fish and seafood"],
        "threshold_kcal": 64.28,
        "points": 1
    },
    "I_MED_13_nuts": {
        "type": "min_kcal_per_day",
        "categories": ["Nuts, seeds, and products"],
        "threshold_kcal": 77.14,
        "points": 1
    },
    "I_MED_14_hummus_tahini": {
        "type": "min_kcal_per_day",
        "categories": ["Med Oil and fats"],
        "threshold_kcal": 34.28,
        "points": 1
    },
    "I_MED_15_17_sweets_snacks_baked_goods": {
        "type": "graded_max_kcal_per_day",
        "categories": ["sweets", "Snacks", "baked goods"],
        "thresholds": [
            {
                "max_kcal": 85.71,
                "points": 3
            },
            {
                "max_kcal": 142.86,
                "points": 2
            },
            {
                "max_kcal": 228.57,
                "points": 1
            },
            {
                "max_kcal": None,
                "points": 0
            }
        ]
    }
}

AHEI_2010_CONFIG = {
    "vegetables": {
        "type": "linear_positive",
        "categories": ["Vegetables"],
        "serving_kcal": 30,
        "min_servings": 0,
        "max_servings": 5,
        "max_points": 10
    },
    "fruit": {
        "type": "linear_positive",
        "categories": ["Fruits"],
        "serving_kcal": 70,
        "min_servings": 0,
        "max_servings": 4,
        "max_points": 10
    },
    "whole_grains": {
        "type": "linear_positive_sex_specific",
        "categories": ["Bread_wholewheat", "Pasta, Grains and Side dishes_wholewheat", "Cereals_wholewheat"],
        "min_value": 0,
        "max_value_female": 75,
        "max_value_male": 90,
        "max_points": 10
    },
    "sugar_sweetened_beverages_and_fruit_juice": {
        "type": "linear_negative",
        "categories": ["fruit juices and soft drinks"],
        "serving_kcal": 70,
        "min_servings": 0,
        "max_servings": 1,
        "max_points": 10
    },
    "nuts_and_legumes": {
        "type": "linear_positive",
        "categories": ["Pulses and products", "Nuts, seeds, and products"],
        "serving_kcal": 100,
        "min_servings": 0,
        "max_servings": 1,
        "max_points": 10
    },
    "red_processed_meat": {
        "type": "linear_negative",
        "categories": ["Beef, veal, lamb, and other meat products", "Proccessed  meat products"],
        "serving_kcal": 220,
        "min_servings": 0,
        "max_servings": 1.5,
        "max_points": 10
    }
}

HPDI_CONFIG = {
    "positive_groups": {
        "whole_grains": ["Pasta, Grains and Side dishes_wholewheat", "Bread_wholewheat", "Cereals_wholewheat"],
        "fruits_excluding_fruit_juice": ["Fruits", "Canned veg and fruits"],
        "vegetables_excluding_potatoes": ["Vegetables"],
        "nuts": ["Nuts, seeds, and products"],
        "legumes": ["Pulses and products"],
        "vegetable_oils": ["Med Oil and fats"],
        "tea_and_coffee": ["Drinks"]
    },
    "less_healthy_plant_groups": {
        "fruit_juices": ["fruit juices and soft drinks"],
        "sugar_sweetened_beverages": ["fruit juices and soft drinks"],
        "refined_grains": ["Pasta, Grains and Side dishes", "Industrialized vegetarian food ready to eat", "Cereals", "Bread"],
        "potatoes": ["Potatoes"],
        "sweets_and_desserts": ["sweets", "baked goods", "Snacks"]
    },
    "animal_based_groups": {
        "red_processed_meat": ["Beef, veal, lamb, and other meat products", "Proccessed  meat products"],
        "poultry": ["Poultry and its products"],
        "fish_and_seafood": ["Fish and seafood"],
        "dairy": ["Hard cheese", "milk, cream cheese and yogurts", "sweet milk products"],
        "eggs": ["Eggs and their products"],
        "animal_fats": ["Butter"]
    }
}

OTHER_PATTERN_CONFIG = {
    "WFPB": {
        "supp2_row": "WFPB",
        "base_food_thresholds": {
            "Vegetables": {
                "categories": ["Vegetables"],
                "type": "absolute_kcal",
                "threshold": 100
            },
            "Fruits": {
                "categories": ["Fruits"],
                "type": "absolute_kcal",
                "threshold": 100
            },
            "Whole grains": {
                "categories": ["Pasta, Grains and Side dishes_wholewheat", "Bread_wholewheat", "Cereals_wholewheat"],
                "type": "pct_total_energy",
                "threshold": 0.05
            },
            "Pulses": {
                "categories": ["Pulses and products"],
                "type": "pct_total_energy",
                "threshold": 0.05
            },
            "Nuts and seeds": {
                "categories": ["Nuts, seeds, and products"],
                "type": "pct_total_energy",
                "threshold": 0.05
            }
        },
        "moderation_food_thresholds": {}
    },
    "Carnivore": {
        "supp2_row": "Carnivore",
        "base_food_thresholds": {},
        "moderation_food_thresholds": {
            "Hard cheese + milk cream cheese and yogurts": {
                "categories": ["Hard cheese", "milk, cream cheese and yogurts"],
                "type": "pct_total_energy",
                "threshold": 0.5
            }
        }
    },
    "Vegan": {
        "supp2_row": "Vegan",
        "base_food_thresholds": {},
        "moderation_food_thresholds": {}
    },
    "Vegetarian": {
        "supp2_row": "Vegetarian",
        "base_food_thresholds": {},
        "moderation_food_thresholds": {}
    },
    "Pescatarian": {
        "supp2_row": "Pescatarian",
        "base_food_thresholds": {},
        "moderation_food_thresholds": {}
    }
}
