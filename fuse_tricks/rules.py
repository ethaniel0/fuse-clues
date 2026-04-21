from dataclasses import dataclass
from fuse_tricks.conditions import Condition
from fuse_tricks.actions import Action


@dataclass
class Rule:
    condition: Condition
    actions: list[Action]

    def execute_actions(self, ctx: dict):
        outputs = {}
        for action in self.actions:
            out = action.execute(ctx)
            outputs.update(out)
        return outputs
