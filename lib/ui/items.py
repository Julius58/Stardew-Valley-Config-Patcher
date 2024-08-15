from enum import Enum
from typing import Optional, Callable
from consolemenu import ConsoleMenu
from consolemenu.items import MenuItem
from consolemenu.prompt_utils import PromptUtils

class InputItem(MenuItem):
    _value: str = ''

    def __init__(self, item_text: str | Callable[[], str], prompt: str | Callable[[], str], menu: ConsoleMenu, menu_char: str | None = None) -> None:
        super().__init__(item_text, menu, False, menu_char)
        assert menu is not None
        self.prompt_utils = PromptUtils(menu.screen)
        self.prompt = prompt

    def get_prompt(self) -> str:
        return self.prompt() if callable(self.prompt) else self.prompt

    def get_text(self) -> str:
        text = super().get_text()
        return "%s\nCurrent value: %s" % (text, self._value)

    def action(self) -> None:
        assert self.menu is not None
        input_result = self.prompt_utils.input(self.get_prompt())
        self._value = input_result.input_string

    def get_return(self) -> str:
        return self._value

class OptionalOptionItem(MenuItem):
    _value: Optional[bool] = None
    _FALSE_CHAR = 'X'
    _TRUE_CHAR = 'O'
    _NOT_SET_CHAR = ' '

    def get_checkbox(self) -> str:
        match self._value:
            case False:
                s = self._FALSE_CHAR
            case True:
                s = self._TRUE_CHAR
            case None:
                s = self._NOT_SET_CHAR
            case _:
                raise ValueError
            
        return '[%s]' % s
    
    def get_text(self) -> str:
        return "%s %s" % (self.get_checkbox(), super().get_text())

    def action(self) -> None:
        match self._value:
            case False:
                self._value = True
            case True:
                self._value = None
            case None:
                self._value = False
            case _:
                raise ValueError

    def get_return(self) -> Optional[bool]:
        return self._value

class Direction(Enum):
    CONFIG = True
    IGNORE = None
    PATCH = False

    @classmethod
    def from_value(cls, value: Optional[bool]) -> 'Direction':
        match value:
            case cls.CONFIG.value:
                return cls.CONFIG
            case cls.IGNORE.value:
                return cls.IGNORE
            case cls.PATCH.value:
                return cls.PATCH
            case _:
                raise ValueError

class DirectionSelectionItem(OptionalOptionItem):
    _TRUE_CHAR = 'Config'
    _NOT_SET_CHAR = 'Ignore'
    _FALSE_CHAR = 'Patch'
    _key: str

    def __init__(self, key: str, on_disk_value: str, patch_value: str, default_value: Direction = Direction.IGNORE, menu: ConsoleMenu | None = None, menu_char: str | None = None) -> None:
        super().__init__(f'{key}:\nConfig Value: {on_disk_value}\nPatch Value: {patch_value}', menu=menu, should_exit=False, menu_char=menu_char)
        self._key = key
        self._value = default_value.value

    def get_return(self) -> Direction:
        return Direction.from_value(self._value)
            
    def get_key(self) -> str:
        return self._key
    
class OptionItem(OptionalOptionItem):
    def __init__(self, text: str | Callable[[], str], menu: ConsoleMenu | None = None, should_exit: bool = False, menu_char: str | None = None) -> None:
        super().__init__(text, menu, should_exit, menu_char)
        self._value = False

    def action(self) -> None:
        self._value = not self._value

    def get_return(self) -> bool:
        assert self._value is not None

        return self._value
    
class ValidatorItem(MenuItem):
    def __init__(self, text: str | Callable[[], str], menu: ConsoleMenu | None = None, menu_char: str | None = None) -> None:
        super().__init__(text, menu, False, menu_char)

    def validate(self) -> bool:
        return True

    def action(self) -> None:
        self.should_exit = self.validate()