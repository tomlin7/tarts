from __future__ import annotations

import typing as t

from pydantic import BaseModel, PrivateAttr

if t.TYPE_CHECKING:
    from .client import Client

from .structs import (
    CallHierarchyItem,
    CompletionList,
    ConfigurationItem,
    Diagnostic,
    DocumentSymbol,
    FoldingRange,
    InlayHint,
    JSONDict,
    Location,
    LocationLink,
    MarkedString,
    MarkupContent,
    MessageActionItem,
    MessageType,
    ProgressToken,
    ProgressValue,
    Range,
    Registration,
    SignatureInformation,
    SymbolInformation,
    TextDocumentEdit,
    TextEdit,
    WorkDoneProgressBeginValue,
    WorkDoneProgressEndValue,
    WorkDoneProgressReportValue,
    WorkspaceFolder,
)

Id = t.Union[int, str]


class Event(BaseModel):
    """Base class for all events."""

    pass


class ResponseError(Event):
    """Base class for all response errors.

    Args:
        message_id (Optional[Id]): The message ID.
        code (int): The error code.
        message (str): The error message.
        data (Union[str, int, float, bool, List[Any], Dict[str, Any], None]): The error data.
    """

    message_id: t.Optional[Id]
    code: int
    message: str
    data: t.Optional[t.Union[str, int, float, bool, t.List[t.Any], JSONDict, None]]


class ServerRequest(Event):
    """Base class for all server requests.

    Args:
        _client (Client): The client instance.
        _id (Id): The request ID.
    """

    _client: Client = PrivateAttr()
    _id: Id = PrivateAttr()


class ServerNotification(Event):
    """Base class for all server notifications."""

    pass


class Initialized(Event):
    """The initialized notification is sent from the client to the server after the client received the result
    of the initialize request but before the client is sending any other request or notification to the server.

    Args:
        capabilities (JSONDict): The capabilities of the client (editor).
    """

    capabilities: JSONDict


class Shutdown(Event):
    """The shutdown request is sent from the client to the server. It asks the server to shut down."""

    pass


class ShowMessage(ServerNotification):
    """The show message notification is sent from a server to a client to ask the client to display a particular message
    in the user interface.

    Args:
        type (MessageType): The message type.
        message (str): The message to be shown.
    """

    type: MessageType
    message: str


class ShowMessageRequest(ServerRequest):
    """The show message request is sent from a server to a client to ask the client to display a particular message
    in the user interface.

    Methods:
        reply: Reply to the ShowMessageRequest with the user's selection.

    Args:
        type (MessageType): The message type.
        message (str): The message to be shown.
        actions (Optional[List[MessageActionItem]]): The actions to be shown.
    """

    type: MessageType
    message: str
    actions: t.Optional[t.List[MessageActionItem]]

    def reply(self, action: t.Optional[MessageActionItem] = None) -> None:
        """
        Reply to the ShowMessageRequest with the user's selection.

        No bytes are actually returned from this method, the reply's bytes
        are added to the client's internal send buffer.
        """
        self._client._send_response(
            id=self._id, result=action.dict() if action is not None else None
        )


class LogMessage(ServerNotification):
    """The log message notification is sent from the server to the client to ask the client to log a particular message.

    Args:
        type (MessageType): The message type.
        message (str): The message to be logged.
    """

    type: MessageType
    message: str


class WorkDoneProgressCreate(ServerRequest):
    """The work done progress create request is sent from the server to the client to ask the client to create a
    work done progress.

    Methods:
        reply: Reply to the WorkDoneProgressCreate request.

    Args:
        token (ProgressToken): The progress token."""

    token: ProgressToken

    def reply(self) -> None:
        """Reply to the WorkDoneProgressCreate request."""

        self._client._send_response(id=self._id, result=None)


class Progress(ServerNotification):
    """Base class for all progress notifications.

    Args:
        token (ProgressToken): The progress token.
        value (ProgressValue): The progress value.
    """

    token: ProgressToken
    value: ProgressValue


class WorkDoneProgress(Progress):
    """Base class for all work done progress notifications.

    Args:
        token (ProgressToken): The progress token.
        value (ProgressValue): The progress value.
    """

    pass


class WorkDoneProgressBegin(WorkDoneProgress):
    """The work done progress begin notification is sent from the server to the client to begin a progress.

    Args:
        value (WorkDoneProgressBeginValue): The progress value.
    """

    value: WorkDoneProgressBeginValue


class WorkDoneProgressReport(WorkDoneProgress):
    """The work done progress report notification is sent from the server to the client to report progress.

    Args:
        value (WorkDoneProgressReportValue): The progress value.
    """

    value: WorkDoneProgressReportValue


class WorkDoneProgressEnd(WorkDoneProgress):
    """The work done progress end notification is sent from the server to the client to end a progress.

    Args:
        value (WorkDoneProgressEndValue): The progress value.
    """

    value: WorkDoneProgressEndValue


# XXX: should these two be just Events or?
class Completion(Event):
    """The completion request is sent from the client to the server to compute completion items at a given cursor position.

    Args:
        message_id (Optional[Id]): The message ID.
        completion_list (Optional[CompletionList]): The completion list.
    """

    message_id: Id
    completion_list: t.Optional[CompletionList]


# XXX: not sure how to name this event.
class WillSaveWaitUntilEdits(Event):
    """The will save wait until edits request is sent from the client to the server before the document is actually saved.

    Args:
        message_id (Optional[Id]): The message ID.
        edits (Optional[List[TextEdit]]): The edits.
    """

    edits: t.Optional[t.List[TextEdit]]


class PublishDiagnostics(ServerNotification):
    """The publish diagnostics notification is sent from the server to the client to signal results of validation runs.

    Args:
        uri (str): The URI for which diagnostic information is reported.
        version (Optional[int]): The version number of the document the diagnostics are published for.
        diagnostics (List[Diagnostic]): The diagnostics.
    """

    uri: str
    version: t.Optional[int]
    diagnostics: t.List[Diagnostic]


class Hover(Event):
    """The hover request is sent from the client to the server to request hover information at a given text document position.

    Args:
        message_id (Optional[Id]): The message ID.
        contents (Union[List[Union[MarkedString, str]], MarkedString, MarkupContent, str]): The hover contents.
        range (Optional[Range]): The hover range.
    """

    message_id: t.Optional[Id]  # custom...
    contents: t.Union[
        t.List[t.Union[MarkedString, str]], MarkedString, MarkupContent, str
    ]
    range: t.Optional[Range]


class SignatureHelp(Event):
    """The signature help request is sent from the client to the server to request signature information at a given cursor position.

    Methods:
        get_hint_str: Get the signature help hint string.

    Args:
        message_id (Optional[Id]): The message ID.
        signatures (List[SignatureInformation]): The signatures.
        activeSignature (Optional[int]): The active signature.
        activeParameter (Optional[int]): The active parameter.
    """

    message_id: t.Optional[Id]  # custom...
    signatures: t.List[SignatureInformation]
    activeSignature: t.Optional[int]
    activeParameter: t.Optional[int]

    def get_hint_str(self) -> t.Optional[str]:
        """Get the signature help hint string."""

        if len(self.signatures) == 0:
            return None
        active_sig = self.activeSignature or 0
        sig = self.signatures[active_sig]
        return sig.label


class Definition(Event):
    """The definition request is sent from the client to the server to resolve the definition location of a symbol at a given text document position.

    Args:
        message_id (Optional[Id]): The message ID.
        result (Union[Location, List[Union[Location, LocationLink]], None]): The definition location.
    """

    message_id: t.Optional[Id]
    result: t.Union[Location, t.List[t.Union[Location, LocationLink]], None]


class WorkspaceEdit(Event):
    """The workspace edit is sent from the server to the client to modify resource on the client side.

    Args:
        message_id (Optional[Id]): The message ID.
        changes (Optional[Dict[str, List[TextEdit]]]): The changes.
        documentChanges (Optional[List[TextDocumentEdit]]): The document changes.
    """

    message_id: t.Optional[Id]
    changes: t.Optional[t.Dict[str, TextEdit]]
    documentChanges: t.Optional[t.List[TextDocumentEdit]]


# result is a list, so putting in a custom class
class References(Event):
    """The references request is sent from the client to the server to resolve project-wide references for the symbol denoted by the given text document position.

    Args:
        message_id (Optional[Id]): The message ID.
        result (List[Location]): The references.
    """

    result: t.Union[t.List[Location], None]


class MCallHierarchItems(Event):
    """The call hierarchy request is sent from the client to the server to resolve items for a given text document position.

    Args:
        message_id (Optional[Id]): The message ID.
        result (Union[List[CallHierarchyItem], None]): The call hierarchy items.
    """

    result: t.Union[t.List[CallHierarchyItem], None]


class Implementation(Event):
    """The implementation request is sent from the client to the server to resolve the implementation location of a symbol at a given text document position.

    Args:
        message_id (Optional[Id]): The message ID.
        result (Union[Location, List[Union[Location, LocationLink]], None]): The implementation location.
    """

    result: t.Union[Location, t.List[t.Union[Location, LocationLink]], None]


class MWorkspaceSymbols(Event):
    """The workspace symbols request is sent from the client to the server to list project-wide symbols matching the query string.

    Args:
        message_id (Optional[Id]): The message ID.
        result (List[SymbolInformation]): The symbols.
    """

    result: t.Union[t.List[SymbolInformation], None]


class MFoldingRanges(Event):
    """The folding ranges request is sent from the client to the server to return all folding ranges found in a given text document.

    Args:
        message_id (Optional[Id]): The message ID.
        result (List[FoldingRange]): The folding ranges.
    """

    message_id: t.Optional[Id]
    result: t.Optional[t.List[FoldingRange]]


class MInlayHints(Event):
    """The inlay hints request is sent from the client to the server to return inlay hints for a specific file.

    Args:
        message_id (Optional[Id]): The message ID.
        result (List[InlayHint]): The inlay hints.
    """

    message_id: t.Optional[Id]
    result: t.Optional[t.List[InlayHint]]


class MDocumentSymbols(Event):
    """The document symbols request is sent from the client to the server to return symbols of a given text document.

    Args:
        message_id (Optional[Id]): The message ID.
        result (Union[List[SymbolInformation], List[DocumentSymbol], None]): The symbols.
    """

    message_id: t.Optional[Id]
    result: t.Union[t.List[SymbolInformation], t.List[DocumentSymbol], None]


class Declaration(Event):
    """The declaration request is sent from the client to the server to resolve the declaration location of a symbol at a given text document position.

    Args:
        message_id (Optional[Id]): The message ID.
        result (Union[Location, List[Union[Location, LocationLink]], None]): The declaration location.
    """

    result: t.Union[Location, t.List[t.Union[Location, LocationLink]], None]


class TypeDefinition(Event):
    """The type definition request is sent from the client to the server to resolve the type definition location of a symbol at a given text document position.

    Args:
        message_id (Optional[Id]): The message ID.
        result (Union[Location, List[Union[Location, LocationLink]], None]): The type definition location.
    """

    result: t.Union[Location, t.List[t.Union[Location, LocationLink]], None]


class RegisterCapabilityRequest(ServerRequest):
    """The register capability request is sent from the client to the server to register a capability.

    Methods:
        reply: Reply to the RegisterCapabilityRequest.

    Args:
        registrations (List[Registration]): The registrations.
    """

    registrations: t.List[Registration]

    def reply(self) -> None:
        """Reply to the RegisterCapabilityRequest."""
        self._client._send_response(id=self._id, result={})


class DocumentFormatting(Event):
    """The document formatting request is sent from the client to the server to format a whole document.

    Args:
        message_id (Optional[Id]): The message ID.
        result (List[TextEdit]): The text edits.
    """

    message_id: t.Optional[Id]
    result: t.Union[t.List[TextEdit], None]


class WorkspaceFolders(ServerRequest):
    """The workspace folders request is sent from the client to the server to fetch the workspace folders.

    Methods:
        reply: Reply to the WorkspaceFolders with workspace

    Args:
        message_id (Optional[Id]): The message ID.
        result (Optional[List[WorkspaceFolder]]): The workspace folders.
    """

    result: t.Optional[t.List[WorkspaceFolder]]

    def reply(self, folders: t.Optional[t.List[WorkspaceFolder]] = None) -> None:
        """
        Reply to the WorkspaceFolder with workspace folders.

        No bytes are actually returned from this method, the reply's bytes
        are added to the client's internal send buffer.
        """
        self._client._send_response(
            id=self._id,
            result=[f.dict() for f in folders] if folders is not None else None,
        )


class ConfigurationRequest(ServerRequest):
    """The configuration request is sent from the client to the server to fetch configuration settings.

    Methods:
        reply: Reply to the ConfigurationRequest with configuration items.

    Args:
        message_id (Optional[Id]): The message ID.
        result (List[ConfigurationItem]): The configuration items.
    """

    items: t.List[ConfigurationItem]

    def reply(self, result: t.List[t.Any] = []) -> None:
        """
        Reply to the ConfigurationRequest with configuration items.

        No bytes are actually returned from this method, the reply's bytes
        are added to the client's internal send buffer.
        """
        self._client._send_response(id=self._id, result=result)
