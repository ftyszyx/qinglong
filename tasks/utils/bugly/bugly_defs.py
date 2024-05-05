from typing import List
from pydantic import BaseModel


class BuglyAppInfo(BaseModel):
    appName: str = ""
    appId: str = ""
    pid: int = 0  #1:android 2:ios
    logoUrl: str = ""
    type: int = 0
    isSdkApp: int = 0
    appKey: str = ""
    appFrom: int = 0
    isGray: bool = False
    createTime: str = ""
    userdataEnable: int = 0
    ownerId: str = ""
    memberCount: int = 0
    enableUserAuit: int = 0
    showAuit: int = 0
    betaEnable: int = 0


class CrashHourInfo(BaseModel):
    appId: str = ""
    hour: int = 0
    platformId: int = 0
    issueId: int = 0
    date: str = ""
    crashNum: int = 0
    crashUser: int = 0
    accessUser: int = 0
    accessNum: int = 0
    state: int = 0
    exceptionName: str = ""
    crash_num_rate: float = 0  # 次数崩溃率
    crash_user_rate: float = 0  # 设备崩溃率


class IssueVersionInfo(BaseModel):
    version: str = ""
    count: int = 0
    deviceCount: int = 0


class TagInfo(BaseModel):
    tagId: int = 0
    tagType: int = 0
    tagCount: int = 0
    tagName: str = ""


class IssueInfo(BaseModel):
    appId: str = ""
    crashNum: int = 0
    exceptionName: str = ""
    exceptionMessage: str = ""
    keyStack: str = ""
    lastestUploadTime: str = ""
    issueId: str = ""
    imeiCount: int = 0
    processor: str = ""
    status: int = 0
    tagInfoList: List[TagInfo] = []
    count: int = 0
    version: str = ""
    ftName: str = ""


class CrashMap(BaseModel):
    id: str = ""
    issueId: int = 0
    productVersion: str = ""
    model: str = ""
    userId: str = ""
    expName: str = ""
    expMessage: str = ""
    deviceId: str = ""
    crashCount: int = 0
    type: str = ""
    appUUID: str = ""
    processName: str = ""
    isRooted: str = ""
    retraceStatus: int = 0
    uploadTime: str = ""
    crashTime: str = ""
    mergeVersion: str = ""
    messageVersion: str = ""
    isSystemStack: int = 0
    rqdUuid: str = ""
    sysRetracStatus: int = 0
    appInBack: str = ""
    cpuType: str = ""
    isRestore: bool = False
    subVersionIssueId: int = 0
    crashId: int = 0
    bundleId: str = ""
    sdkVersion: str = ""
    osVer: str = ""
    expAddr: str = ""
    sessionId: str = ""
    archVersion: str = ""
    appBaseAddr: str = ""
    appInfo: str = ""
    threadName: str = ""
    detailDir: str = ""
    memSize: str = ""
    diskSize: str = ""
    freeMem: str = ""
    freeStorage: str = ""
    country: str = ""
    channelId: str = ""
    startTime: str = ""
    isReRetrace: int = 0
    isReClassify: int = 0
    retraceCount: int = 0
    callStack: str = ""
    retraceCrashDetail: str = ""
    apn: str = ""
    appInAppstore: bool = False
    modelOriginalName: str = ""


class CrashFilelMap(BaseModel):
    fileName: str = ""
    codeType: int = 0
    fileType: int = 0
    fileContent: str = ""


class CrashDetailMap(BaseModel):
    attatchCount: int = 0
    stackName: str = ""
    retraceCrashDetail: str = ""
    freeMem: int = 0
    appBaseAddr: str = ""
    battery: int = 0
    archVersion: str = ""
    attachName: str = ""
    id: str = ""
    fileList: List[CrashFilelMap] = []
    srcIp: str = ""
    freeSdCard: int = 0
    isGZIP: int = 0
    cpu: int = 0
    uploadTime: str = ""
    userKey: str = ""
    contactAll: str = ""
    callStack: str = ""
    fileDir: str = ""
    sdkVersion: str = ""
    freeStorage: int = 0


class CrashAttachInfo(BaseModel):
    fileName: str = ""
    fileType: int = 0
    content: str = ""


class CrashAttachmentInfo(BaseModel):
    ttachName: str = ""
    stackName: str = ""
    attachList: List[CrashAttachInfo] = []
    sysLogs: List[str] = []
    userLogs: List[str] = []


class CrashInfo(BaseModel):
    productVersion: str = ""
    model: str = ""
    id: str = ""
    uploadTime: str = ""
    crashId: int = 0
    osVer: str = ""
    issueId: str = ""
    appId: str = ""
    url: str = ""
    crashMap: CrashMap = None
    detailMap: CrashDetailMap = None
    attachList: List[CrashAttachInfo] = []
    attach: CrashAttachmentInfo = None
