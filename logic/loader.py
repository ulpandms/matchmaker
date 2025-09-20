import importlib

def load_logic(game_type, game_format, players_count, courts_count):
    """
    Dynamically load a logic module depending on configuration.
    Example: logic/doubles/mexicano/6p1c.py
    """

    base_path = "logic"

    # Normalize values
    gt = (game_type or "").strip().lower()
    gf = (game_format or "").strip().lower()
    pc = int(players_count or 0)
    cc = int(courts_count or 0)

    # Build path like logic.doubles.mexicano.6p1c
    module_path = f"{base_path}.{gt}.{gf}.{pc}p{cc}c"

    print("=== [Logic Loader DEBUG] ===")
    print("game_type    :", game_type)
    print("game_format  :", game_format)
    print("players_count:", players_count)
    print("courts_count :", courts_count)
    print("module_path  :", module_path)
    print("============================")

    try:
        module = importlib.import_module(module_path)
        print(f"[Logic Loader] ✅ Loaded {module_path}")
        return module
    except ImportError as e:
        print(f"[Logic Loader] ❌ Could not load {module_path}")
        print("Error:", e)
        return None
