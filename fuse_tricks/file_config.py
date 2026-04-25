from dataclasses import dataclass, field
from fuse_tricks.rules import Rule
from fuse_tricks.conditions import Condition

@dataclass
class DirectoryMap:
    condition: Condition
    map_to: str

@dataclass
class FileConfig:
    hooks: dict[str, list[Rule]]
    directory_map: DirectoryMap | None = None
    state: dict = field(default_factory=dict)

    def evaluate_hook(self, operation: str, ctx: dict):
        rules = self.hooks.get(operation, [])
        ctx["state"] = self.state
        for rule in rules:
            # print(f"Evaluating rule with condition: {rule.condition} and actions: {rule.actions}, with context: {ctx}")
            if rule.condition.evaluate(ctx):
                # print('Condition met, executing actions...')
                return rule.execute_actions(ctx)
        return None
