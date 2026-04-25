from dataclasses import dataclass
from engine.conditions import Condition
from engine.actions import Action


@dataclass
class Rule:
    condition: Condition
    actions: list[Action]

    def execute_actions(self, ctx: dict):
        outputs = {}
        for action in self.actions:
            # print(f"Executing action: {action}, with context: {ctx}")
            out = action.execute(ctx)
            outputs.update(out)
        return outputs
