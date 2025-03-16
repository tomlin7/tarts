import enum
import typing as t

from pydantic import BaseModel, Field
from typing_extensions import Literal

# XXX: Replace the non-commented-out code with what's commented out once nested
# types become a thing in mypy.
# JSONValue = t.Union[None, str, int,
#                     t.List['JSONValue'], t.Dict[str, 'JSONValue']]
# JSONDict = t.Dict[str, JSONValue]
JSONDict = t.Dict[str, t.Any]
JSONList = t.List[t.Any]

Id = t.Union[int, str]

ProgressToken = t.Union[int, str]


class Request(BaseModel):
    """Base class for LSP requests.

    Args:
        method(str): The method of the request.
        id (Id): The request ID.
        params (list | JSONDict): The parameters of the request.
    """
    method: str
    id: t.Optional[Id] = None
    params: t.Optional[JSONDict] = None

class Response(BaseModel):
    """Base class for LSP responses.

    The `result` field is either a list of values or a dictionary.

    Args:
        id (Id): The request ID.
        result(List[Any] | JSONDict): The result of the request.
        error: The error that occurred during the request.
    """
    id: t.Optional[Id] = None
    result: t.Optional[t.Union[t.List[t.Any], JSONDict]] = None
    error: t.Optional[JSONDict] = None

class MessageType(enum.IntEnum):
    """Message type for LSP notifications.

    Attributes:
        ERROR: Error message.
        WARNING: Warning message.
        INFO: Information message.
        LOG: Log message.
        DEBUG: Debug message.
    """

    ERROR = 1
    WARNING = 2
    INFO = 3
    LOG = 4
    DEBUG = 5


class MessageActionItem(BaseModel):
    """Action item for LSP notifications.

    Args:
        title(str): The title of the action.
    """

    title: str


class TextDocumentItem(BaseModel):
    """Text document item for LSP notifications.

    Args:
        uri(str): The URI of the document.
        languageId(str): The language ID of the document.
        version(int): The version of the document.
        text(str): The text of the document.
    """

    uri: str
    languageId: str
    version: int
    text: str


class TextDocumentIdentifier(BaseModel):
    """Text document identifier for LSP requests.

    Args:
        uri(str): The URI of the document
    """

    uri: str


class OptionalVersionedTextDocumentIdentifier(TextDocumentIdentifier):
    """Text document identifier with an optional version for LSP requests.

    Args:
        uri(str): The URI of the document
        version(int): The version of the document
    """

    version: t.Optional[int]


class VersionedTextDocumentIdentifier(TextDocumentIdentifier):
    """Text document identifier with a version for LSP notifications.

    Args:
        uri(str): The URI of the document
        version(int): The version of the document
    """

    version: t.Optional[int]


# Sorting tip:  sorted(positions, key=(lambda p: p.as_tuple()))
class Position(BaseModel):
    """Position in a text document.

    Methods:
        as_tuple: Return the position as a tuple.

    Args:
        line (int): The line number (0-based).
        character (int): The character number (0-based).
    """

    # NB: These are both zero-based.
    line: int
    character: int

    def as_tuple(self) -> t.Tuple[int, int]:
        """Return the position as a tuple.

        Returns:
            Tuple[int, int]: The position as a tuple.
        """

        return (self.line, self.character)


class Range(BaseModel):
    """Represents a range in a text document.

    Args:
        start (Position): The start position of the range.
        end (Position): The end position of the range.
    """

    start: Position
    end: Position

    def calculate_length(self, text: str) -> int:
        """Calculate the length of the range in the given text.

        Args:
            text (str): The text to calculate the range length in.

        Returns:
            int: The length of the range.
        """
        text_lines = text.splitlines()

        if self.end.line == self.start.line:
            line = text_lines[self.start.line]
            return len(line[self.start.character : self.end.character])
        else:
            total = 0

            total += len(text_lines[self.start.line][self.start.character :])

            for line_number in range(self.start.line + 1, self.end.line):
                total += len(text_lines[line_number])

            total += len(text_lines[self.end.line][: self.end.character])

            return total


class TextDocumentContentChangeEvent(BaseModel):
    """Represents a content change event in a text document.

    Args:
        text (str): The new text of the document.
        range (Optional[Range]): The range of the document that changed.
        rangeLength (Optional[int]): The length of the range that changed (deprecated, use .range).
    """

    text: str
    range: t.Optional[Range]
    rangeLength: t.Optional[int]  # deprecated, use .range

    def model_dump(self, **kwargs: t.Any) -> t.Dict[str, t.Any]:
        """Return a dictionary representation of the event.

        Returns:
            Dict[str, Any]: A dictionary representation of the event.
        """
        d = super().model_dump(**kwargs)

        # vscode-css server requires un-filled values to be absent
        # TODO: add vscode-css to tests
        if self.rangeLength is None:
            del d["rangeLength"]
        if self.range is None:
            del d["range"]
        return d

    @classmethod
    def range_change(
        cls,
        change_start: Position,
        change_end: Position,
        change_text: str,
        old_text: str,
    ) -> "TextDocumentContentChangeEvent":
        """
        Create a TextDocumentContentChangeEvent reflecting the given changes.

        Args:
            change_start (Position): The start position of the change.
            change_end (Position): The end position of the change.
            change_text (str): The new text for the changed range.
            old_text (str): The old text of the document.

        Returns:
            TextDocumentContentChangeEvent: A new instance representing the change.

        Note:
            If you're creating a list of TextDocumentContentChangeEvent based on many changes,
            `old_text` must reflect the state of the text after all previous change events happened.
        """
        change_range = Range(start=change_start, end=change_end)
        return cls(
            range=change_range,
            rangeLength=change_range.calculate_length(old_text),
            text=change_text,
        )

    @classmethod
    def whole_document_change(
        cls, change_text: str
    ) -> "TextDocumentContentChangeEvent":
        """Create a TextDocumentContentChangeEvent for a whole document change.

        Args:
            change_text (str): The new text of the entire document.

        Returns:
            TextDocumentContentChangeEvent: A new instance representing the whole document change.
        """
        return cls(text=change_text, range=None, rangeLength=None)


class TextDocumentPosition(BaseModel):
    """Represents a position in a text document.

    Args:
        textDocument (TextDocumentIdentifier): The text document.
        position (Position): The position inside the text document.
    """

    textDocument: TextDocumentIdentifier
    position: Position


class CompletionTriggerKind(enum.IntEnum):
    """Defines how the completion was triggered.

    Attributes:
        INVOKED: Completion was triggered by typing an identifier.
        TRIGGER_CHARACTER: Completion was triggered by a trigger character.
        TRIGGER_FOR_INCOMPLETE_COMPLETIONS: Completion was re-triggered as the current completion list is incomplete.
    """

    INVOKED = 1
    TRIGGER_CHARACTER = 2
    TRIGGER_FOR_INCOMPLETE_COMPLETIONS = 3


class CompletionContext(BaseModel):
    """Contains additional information about the context in which a completion request is triggered.

    Args:
        triggerKind (CompletionTriggerKind): How the completion was triggered.
        triggerCharacter (Optional[str]): The trigger character that caused the completion.
    """

    triggerKind: CompletionTriggerKind
    triggerCharacter: t.Optional[str] = None


class MarkupKind(enum.Enum):
    """Describes the content type that a client supports in various result literals like `Hover`, `ParameterInfo` or `CompletionItem`.

    Attributes:
        PLAINTEXT: The primary text to be rendered is to be interpreted as plain text.
        MARKDOWN: The primary text to be rendered is to be interpreted as Markdown.
    """

    PLAINTEXT = "plaintext"
    MARKDOWN = "markdown"


class MarkupContent(BaseModel):
    """Represents a string value which content can be represented in different formats.

    Args:
        kind (MarkupKind): The type of markup used.
        value (str): The content itself.
    """

    kind: MarkupKind
    value: str


class TextEdit(BaseModel):
    """A text edit applicable to a text document.

    Args:
        range (Range): The range of the text document to be manipulated.
        newText (str): The string to be inserted. For delete operations use an empty string.
        annotationId (Optional[str]): An optional identifier of the edit.
    """

    range: Range
    newText: str
    annotationId: t.Optional[str] = None


class TextDocumentEdit(BaseModel):
    """Describes textual changes on a single text document.

    Args:
        textDocument (OptionalVersionedTextDocumentIdentifier): The text document to change.
        edits (List[TextEdit]): The edits to be applied.
    """

    textDocument: OptionalVersionedTextDocumentIdentifier
    edits: t.List[TextEdit]


class Command(BaseModel):
    """Represents a reference to a command.

    Args:
        title (str): Title of the command, like `save`.
        command (str): The identifier of the actual command handler.
        arguments (Optional[List[Any]]): Arguments that the command handler should be invoked with.
    """

    title: str
    command: str
    arguments: t.Optional[t.List[t.Any]]


class InsertTextFormat(enum.IntEnum):
    """Defines whether the insert text in a completion item should be interpreted as plain text or a snippet.

    Attributes:
        PLAIN_TEXT: The primary text should be interpreted as plain text.
        SNIPPET: The primary text should be interpreted as a snippet.
    """

    PLAIN_TEXT = 1
    SNIPPET = 2


class CompletionItemKind(enum.IntEnum):
    """The kind of a completion entry.

    Attributes:
        Various completion item kinds with integer values from 1 to 25.
    """

    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    ENUMMEMBER = 20
    CONSTANT = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPEPARAMETER = 25


class CompletionItemTag(enum.IntEnum):
    """Completion item tags are extra annotations that tweak the rendering of a completion item.

    Attributes:
        DEPRECATED: Renders a completion as obsolete, usually using a strike-out.
    """

    DEPRECATED = 1


class CompletionItem(BaseModel):
    """A completion item represents a text snippet that is proposed to complete text that is being typed.

    Args:
        label (str): The label of this completion item.
        kind (Optional[CompletionItemKind]): The kind of this completion item.
        tags (Optional[CompletionItemTag]): Tags for this completion item.
        detail (Optional[str]): A human-readable string with additional information about this item.
        documentation (Union[str, MarkupContent, None]): A human-readable string that represents a doc-comment.
        deprecated (Optional[bool]): Indicates if this item is deprecated.
        preselect (Optional[bool]): Select this item when showing.
        sortText (Optional[str]): A string that should be used when comparing this item with other items.
        filterText (Optional[str]): A string that should be used when filtering a set of completion items.
        insertText (Optional[str]): A string that should be inserted into a document when selecting this completion.
        insertTextFormat (Optional[InsertTextFormat]): The format of the insert text.
        textEdit (Optional[TextEdit]): An edit which is applied to a document when selecting this completion.
        additionalTextEdits (Optional[List[TextEdit]]): An optional array of additional text edits that are applied when selecting this completion.
        commitCharacters (Optional[List[str]]): An optional set of characters that when pressed while this completion is active will accept it first and then type that character.
        command (Optional[Command]): An optional command that is executed after inserting this completion.
        data (Optional[Any]): A data entry field that is preserved on a completion item between a completion and a completion resolve request.
    """

    label: str
    kind: t.Optional[CompletionItemKind] = None
    tags: t.Optional[CompletionItemTag] = None
    detail: t.Optional[str] = None
    documentation: t.Union[str, MarkupContent, None] = None
    deprecated: t.Optional[bool] = None
    preselect: t.Optional[bool] = None
    sortText: t.Optional[str] = None
    filterText: t.Optional[str] = None
    insertText: t.Optional[str] = None
    insertTextFormat: t.Optional[InsertTextFormat] = None
    textEdit: t.Optional[TextEdit] = None
    additionalTextEdits: t.Optional[t.List[TextEdit]] = None
    commitCharacters: t.Optional[t.List[str]] = None
    command: t.Optional[Command] = None
    data: t.Optional[t.Any] = None


class CompletionList(BaseModel):
    """Represents a collection of completion items to be presented in the editor.

    Args:
        isIncomplete (bool): This list is not complete. Further typing should result in recomputing this list.
        items (List[CompletionItem]): The completion items.
    """

    isIncomplete: bool
    items: t.List[CompletionItem]


class TextDocumentSaveReason(enum.IntEnum):
    """Represents reasons why a text document is saved.

    Attributes:
        MANUAL: Manually triggered, e.g. by the user pressing save, by starting debugging, or by an API call.
        AFTER_DELAY: Automatic after a delay.
        FOCUS_OUT: When the editor lost focus.
    """

    MANUAL = 1
    AFTER_DELAY = 2
    FOCUS_OUT = 3


class Location(BaseModel):
    """Represents a location inside a resource, such as a line inside a text file.

    Args:
        uri (str): The text document's URI.
        range (Range): The range inside the text document.
    """

    uri: str
    range: Range


class LocationLink(BaseModel):
    """Represents a link between a source and a target location.

    Args:
        originSelectionRange (Optional[Range]): Span of the origin of this link.
        targetUri (str): The target resource identifier of this link.
        targetRange (Range): The full target range of this link.
        targetSelectionRange (Range): The span of the target of this link.
    """

    originSelectionRange: t.Optional[Range] = None
    targetUri: str  # in the spec the type is DocumentUri
    targetRange: Range
    targetSelectionRange: Range


class DiagnosticRelatedInformation(BaseModel):
    """Represents additional information related to a diagnostic.

    Args:
        location (Location): The location of this related diagnostic information.
        message (str): The message of this related diagnostic information.
    """

    location: Location
    message: str


class DiagnosticSeverity(enum.IntEnum):
    """Enumeration of diagnostic severity levels.

    Attributes:
        ERROR (int): Error severity level.
        WARNING (int): Warning severity level.
        INFORMATION (int): Information severity level.
        HINT (int): Hint severity level.
    """

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class CodeDescription(BaseModel):
    """Represents a code description.

    Args:
        href (str): The URI to the code description.
    """

    href: str


class DiagnosticTag(enum.IntEnum):
    """Enumeration of diagnostic tags.

    Attributes:
        UNNECESSARY (int): Unnecessary code.
        DEPRECATED (int): Deprecated code.
    """

    UNNECESSARY = 1
    DEPRECATED = 2


class Diagnostic(BaseModel):
    """Represents a diagnostic, such as a compiler error or warning.

    Args:
        range (Range): The range at which the message applies.
        severity (Optional[DiagnosticSeverity]): The diagnostic's severity.
        code (Optional[Union[int, str]]): The diagnostic's code, which might appear in the user interface.
        codeDescription (Optional[CodeDescription]): An optional code description.
        source (Optional[str]): A human-readable string describing the source of this diagnostic.
        message (str): The diagnostic's message.
        tags (Optional[List[DiagnosticTag]]): Additional metadata about the diagnostic.
        relatedInformation (Optional[List[DiagnosticRelatedInformation]]): Related diagnostic information.
        data (Optional[Any]): Additional structured data about the diagnostic.
    """

    range: Range
    severity: t.Optional[DiagnosticSeverity] = None
    code: t.Optional[t.Union[int, str]] = None
    codeDescription: t.Optional[CodeDescription] = None
    source: t.Optional[str] = None
    tags: t.Optional[t.List[DiagnosticTag]] = None
    message: str
    relatedInformation: t.Optional[t.List[DiagnosticRelatedInformation]] = None
    data: t.Optional[t.Any] = None


class MarkedString(BaseModel):
    """Represents a string with a specific language.

    Args:
        language (str): The language of the string (e.g., 'python', 'javascript').
        value (str): The string value.
    """

    language: str
    value: str


class ParameterInformation(BaseModel):
    """Represents information about a parameter of a callable-signature.

    Args:
        label (Union[str, Tuple[int, int]]): The label of this parameter information.
        documentation (Optional[Union[str, MarkupContent]]): The human-readable doc-comment of this parameter.
    """

    label: t.Union[str, t.Tuple[int, int]]
    documentation: t.Optional[t.Union[str, MarkupContent]] = None


class SignatureInformation(BaseModel):
    """Represents the signature of something callable.

    Args:
        label (str): The label of this signature.
        documentation (Optional[Union[MarkupContent, str]]): The human-readable doc-comment of this signature.
        parameters (Optional[List[ParameterInformation]]): The parameters of this signature.
        activeParameter (Optional[int]): The index of the active parameter.
    """

    label: str
    documentation: t.Optional[t.Union[MarkupContent, str]] = None
    parameters: t.Optional[t.List[ParameterInformation]] = None
    activeParameter: t.Optional[int] = None


class SymbolKind(enum.IntEnum):
    """Enumeration of symbol kinds.

    Attributes:
        FILE (int): A file symbol.
        MODULE (int): A module symbol.
        NAMESPACE (int): A namespace symbol.
        PACKAGE (int): A package symbol.
        CLASS (int): A class symbol.
        METHOD (int): A method symbol.
        PROPERTY (int): A property symbol.
        FIELD (int): A field symbol.
        CONSTRUCTOR (int): A constructor symbol.
        ENUM (int): An enum symbol.
        INTERFACE (int): An interface symbol.
        FUNCTION (int): A function symbol.
        VARIABLE (int): A variable symbol.
        CONSTANT (int): A constant symbol.
        STRING (int): A string symbol.
        NUMBER (int): A number symbol.
        BOOLEAN (int): A boolean symbol.
        ARRAY (int): An array symbol.
        OBJECT (int): An object symbol.
        KEY (int): A key symbol.
        NULL (int): A null symbol.
        ENUMMEMBER (int): An enum member symbol.
        STRUCT (int): A struct symbol.
        EVENT (int): An event symbol.
        OPERATOR (int): An operator symbol.
        TYPEPARAMETER (int): A type parameter symbol.
    """

    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUMMEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPEPARAMETER = 26


class SymbolTag(enum.IntEnum):
    """Enumeration of symbol tags.

    Attributes:
        DEPRECATED (int): Indicates that a symbol is deprecated.
    """

    DEPRECATED = 1


class CallHierarchyItem(BaseModel):
    """Represents an item of a call hierarchy.

    Args:
        name (str): The name of this item.
        kind (SymbolKind): The kind of this item.
        tags (Optional[SymbolTag]): Tags for this item.
        detail (Optional[str]): More detail for this item.
        uri (str): The resource identifier of this item.
        range (Range): The range enclosing this symbol.
        selectionRange (Range): The range that should be selected and revealed when this symbol is being picked.
        data (Optional[Any]): A data entry field that is preserved between a call hierarchy prepare and incoming calls or outgoing calls requests.
    """

    name: str
    kind: SymbolKind
    tags: t.Optional[SymbolTag] = None
    detail: t.Optional[str] = None
    uri: str
    range: Range
    selectionRange: Range
    data: t.Optional[t.Any] = None


class CallHierarchyIncomingCall(BaseModel):
    """Represents an incoming call, as part of the call hierarchy.

    Args:
        from_ (CallHierarchyItem): The item that makes the call.
        fromRanges (List[Range]): The ranges at which the calls appear.
    """

    from_: CallHierarchyItem = Field(alias="from")
    fromRanges: t.List[Range]

    # deprecated
    # class Config:
    #     # 'from' is an invalid field - re-mapping
    #     fields = {"from_": "from"}


class CallHierarchyOutgoingCall(BaseModel):
    """Represents an outgoing call, as part of the call hierarchy.

    Args:
        to (CallHierarchyItem): The item that is called.
        fromRanges (List[Range]): The ranges at which this item is called.
    """

    to: CallHierarchyItem
    fromRanges: t.List[Range]


class TextDocumentSyncKind(enum.IntEnum):
    """Enumeration of text document synchronization kinds.

    Attributes:
        NONE (int): Documents should not be synced at all.
        FULL (int): Documents are synced by always sending the full content of the document.
        INCREMENTAL (int): Documents are synced by sending incremental updates to the document.
    """

    NONE = 0
    FULL = 1
    INCREMENTAL = 2


class SymbolInformation(BaseModel):
    """Represents information about programming constructs like variables, classes, interfaces etc.

    Args:
        name (str): The name of this symbol.
        kind (SymbolKind): The kind of this symbol.
        tags (Optional[List[SymbolTag]]): Tags for this symbol.
        deprecated (Optional[bool]): Indicates if this symbol is deprecated.
        location (Location): The location of this symbol.
        containerName (Optional[str]): The name of the symbol containing this symbol.
    """

    name: str
    kind: SymbolKind
    tags: t.Optional[t.List[SymbolTag]] = None
    deprecated: t.Optional[bool] = None
    location: Location
    containerName: t.Optional[str] = None


class InlayHintLabelPart(BaseModel):
    """Represents a part of an inlay hint.

    Args:
        value (str): The value of this label part.
        tooltip (Optional[Union[str, MarkupContent]]): The tooltip text when you hover over this label part.
        location (Optional[Location]): An optional source code location that represents this label part.
        command (Optional[Command]): An optional command for this label part.
    """

    value: str
    tooltip: t.Optional[t.Union[str, MarkupContent]]
    location: t.Optional[Location] = None
    command: t.Optional[Command] = None


class InlayHintKind(enum.IntEnum):
    """Enumeration of inlay hint kinds.

    Attributes:
        TYPE (int): Type hint.
        PARAMETER (int): Parameter hint.
    """

    TYPE = 1
    PARAMETER = 2


class InlayHint(BaseModel):
    """Represents an inlay hint.

    Args:
        position (Position): The position of this hint.
        label (Union[str, List[InlayHintLabelPart]]): The label of this hint.
        kind (Optional[InlayHintKind]): The kind of this hint.
        textEdits (Optional[List[TextEdit]]): Optional text edits that are performed when accepting this inlay hint.
        tooltip (Optional[Union[str, MarkupContent]]): The tooltip text when you hover over this item.
        paddingLeft (Optional[bool]): Whether the inlay hint should be padded with a space on the left.
        paddingRight (Optional[bool]): Whether the inlay hint should be padded with a space on the right.
        data (Optional[Any]): A data entry field that is preserved on an inlay hint between a textDocument/inlayHint request and a inlayHint/resolve request.
    """

    position: Position
    label: t.Union[str, t.List[InlayHintLabelPart]]
    kind: t.Optional[InlayHintKind] = None
    textEdits: t.Optional[t.List[TextEdit]]
    tooltip: t.Optional[t.Union[str, MarkupContent]]
    paddingLeft: t.Optional[bool] = None
    paddingRight: t.Optional[bool] = None
    data: t.Optional[t.Any] = None


class FoldingRange(BaseModel):
    """Represents a folding range.

    Args:
        startLine (int): The zero-based start line of the range to fold.
        startCharacter (Optional[int]): The zero-based start character of the range to fold.
        endLine (int): The zero-based end line of the range to fold.
        endCharacter (Optional[int]): The zero-based end character of the range to fold.
        kind (Optional[str]): The kind of this folding range (e.g., 'comment', 'imports', 'region').
        collapsedText (Optional[str]): The text that the client should show when the specified range is collapsed.
    """

    startLine: int
    startCharacter: t.Optional[int] = None
    endLine: int
    endCharacter: t.Optional[int] = None
    kind: t.Optional[str] = None  # comment, imports, region
    collapsedText: t.Optional[str] = None


class DocumentSymbol(BaseModel):
    """Represents programming constructs like variables, classes, interfaces etc. that appear in a document.

    Args:
        name (str): The name of this symbol.
        detail (Optional[str]): More detail for this symbol, e.g. the signature of a function.
        kind (SymbolKind): The kind of this symbol.
        tags (Optional[List[SymbolTag]]): Tags for this symbol.
        deprecated (Optional[bool]): Indicates if this symbol is deprecated.
        range (Range): The range enclosing this symbol not including leading/trailing whitespace but everything else.
        selectionRange (Range): The range that should be selected and revealed when this symbol is being picked.
        children (Optional[List[DocumentSymbol]]): Children of this symbol, e.g. properties of a class.
    """

    name: str
    detail: t.Optional[str] = None
    kind: SymbolKind
    tags: t.Optional[t.List[SymbolTag]] = None
    deprecated: t.Optional[bool] = None
    range: Range = Field(..., validate_default=True)
    selectionRange: Range = Field(
        ..., validate_default=True
    )  # Example: symbol.selectionRange.start.as_tuple()
    # https://stackoverflow.com/questions/36193540
    children: t.Optional[t.List["DocumentSymbol"]] = None


DocumentSymbol.model_rebuild()


class Registration(BaseModel):
    """Represents a registration of a capability.

    Args:
        id (str): The id used to register the request. The id can be used to deregister the request again.
        method (str): The method / capability to register for.
        registerOptions (Optional[Any]): Options necessary for the registration.
    """

    id: str
    method: str
    registerOptions: t.Optional[t.Any] = None


class FormattingOptions(BaseModel):
    """Represents formatting options.

    Args:
        tabSize (int): Size of a tab in spaces.
        insertSpaces (bool): Prefer spaces over tabs.
        trimTrailingWhitespace (Optional[bool]): Trim trailing whitespace on a line.
        insertFinalNewline (Optional[bool]): Insert a newline character at the end of the file if one does not exist.
        trimFinalNewlines (Optional[bool]): Trim all newlines after the final newline at the end of the file.
    """

    tabSize: int
    insertSpaces: bool
    trimTrailingWhitespace: t.Optional[bool] = None
    insertFinalNewline: t.Optional[bool] = None
    trimFinalNewlines: t.Optional[bool] = None


class WorkspaceFolder(BaseModel):
    """Represents a workspace folder.

    Args:
        uri (str): The associated URI for this workspace folder.
        name (str): The name of the workspace folder.
    """

    uri: str
    name: str


class ProgressValue(BaseModel):
    """Base class for progress values."""

    pass


class WorkDoneProgressValue(ProgressValue):
    """Base class for work done progress values."""

    pass


class MWorkDoneProgressKind(enum.Enum):
    """Enumeration of work done progress kinds."""

    BEGIN = "begin"
    REPORT = "report"
    END = "end"


class WorkDoneProgressBeginValue(WorkDoneProgressValue):
    """Represents the beginning of a work done progress.

    Args:
        kind (Literal["begin"]): The kind of progress (always "begin" for this class).
        title (str): The title of the progress operation.
        cancellable (Optional[bool]): Whether the operation is cancellable.
        message (Optional[str]): An optional message providing additional details.
        percentage (Optional[int]): An optional initial percentage of the progress.
    """

    kind: Literal["begin"]
    title: str
    cancellable: t.Optional[bool] = None
    message: t.Optional[str] = None
    percentage: t.Optional[int] = None


class WorkDoneProgressReportValue(WorkDoneProgressValue):
    """Represents a report of ongoing work done progress.

    Args:
        kind (Literal["report"]): The kind of progress (always "report" for this class).
        cancellable (Optional[bool]): Whether the operation is cancellable.
        message (Optional[str]): An optional message providing additional details.
        percentage (Optional[int]): An optional updated percentage of the progress.
    """

    kind: Literal["report"]
    cancellable: t.Optional[bool] = None
    message: t.Optional[str] = None
    percentage: t.Optional[int] = None


class WorkDoneProgressEndValue(WorkDoneProgressValue):
    """Represents the end of a work done progress.

    Args:
        kind (Literal["end"]): The kind of progress (always "end" for this class).
        message (Optional[str]): An optional message providing final details or results.
    """

    kind: Literal["end"]
    message: t.Optional[str] = None


class ConfigurationItem(BaseModel):
    """Represents a configuration item.

    Args:
        scopeUri (Optional[str]): The scope URI for this configuration item.
        section (Optional[str]): The section of the configuration this item belongs to.
    """

    scopeUri: t.Optional[str] = None
    section: t.Optional[str] = None
