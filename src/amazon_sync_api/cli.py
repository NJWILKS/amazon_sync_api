"""Explicit plan/execute entry point; summaries exclude private file paths."""
import argparse
import json
import sys

from .core import BackupError, load_config, plan_tree, run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "execute"), default="plan", nargs="?")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    try:
        settings = load_config(args.config)
        if args.command == "plan":
            results = []
            for collection in settings.collections:
                plan = plan_tree(collection, settings.max_files, settings.max_bytes)
                results.append({"collection": collection.id, "files": len(plan.files),
                                "bytes": sum(f.size for f in plan.files),
                                "directories": len(plan.directories),
                                "excluded": len(plan.excluded), "mode": "offline-plan"})
        else:
            from .amazon import Amazon, Transport
            results = run(settings, Amazon(Transport(settings.region, settings.cookies_file)))
        print(json.dumps(results))
        return 0
    except BackupError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception:
        print("Operation failed; inspect private configuration and provider availability", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
