; 本文件编码须是UTF-8 with BOM
; 使用Unicode
Unicode true

; 安装程序初始定义常量
; 版本更新只需要修改[程序名]、[版本号]、[程序路径]
!define PRODUCT_NAME "YOLOv5-Qt"
!define PRODUCT_VERSION "1.0.0"
!define MAIN_PROGRAM_NAME "${PRODUCT_NAME}.exe"
!define PRODUCT_LOCATION "C:\Users\winwain\Documents\GitHub\YOLOv5-Qt\helper\build"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${MAIN_PROGRAM_NAME}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; HKEY_LOCAL_MACHINE
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; 压缩算法
SetCompressor lzma

; ------ MUI 现代界面定义 ------
!include "MUI2.nsh"

; MUI 预定义常量
!define MUI_ABORTWARNING
!define MUI_ICON "${PRODUCT_LOCATION}\img\yologo64.ico"
!define MUI_UNICON "${PRODUCT_LOCATION}\img\yologo64.ico"

; 欢迎页面
; !define MUI_WELCOMEFINISHPAGE_BITMAP "${PRODUCT_LOCATION}\img\MUI_WELCOMEFINISHPAGE_BITMAP.bmp"
!define MUI_WELCOMEPAGE_TEXT "此程序将引导你完成 ${PRODUCT_NAME} ${PRODUCT_VERSION} 的安装！$\r$\n$\r$\n点击 [下一步(N)] 继续。"
!insertmacro MUI_PAGE_WELCOME
; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY
; 安装过程页面
!insertmacro MUI_PAGE_INSTFILES
; 安装完成页面
!define MUI_FINISHPAGE_RUN "$INSTDIR\${MAIN_PROGRAM_NAME}"  ; 安装完后运行程序
; !define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\version.txt"  ; 打开版本升级说明
; !define MUI_FINISHPAGE_SHOWREADME_TEXT "查看升级日志"
!insertmacro MUI_PAGE_FINISH

; 安装卸载过程页面
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${PRODUCT_LOCATION}\img\MUI_WELCOMEFINISHPAGE_BITMAP.bmp"
!insertmacro MUI_UNPAGE_INSTFILES

; 安装界面包含的语言设置
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装预释放文件
!insertmacro MUI_RESERVEFILE_LANGDLL ;Language selection dialog
; ------ MUI 现代界面定义结束 ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${PRODUCT_NAME}-install-${PRODUCT_VERSION}.exe"  ;安装包名
InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"  ; 默认安装目录
InstallDirRegKey HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
ShowInstDetails show
ShowUnInstDetails show
BrandingText "${PRODUCT_NAME} ${PRODUCT_VERSION}"

; 创建开始菜单程序目录
; 创建开始菜单快捷方式
; 创建桌面快捷方式
Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer  ; 更新文件
  File /r "${PRODUCT_LOCATION}\*.*"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}.lnk" "$INSTDIR\${MAIN_PROGRAM_NAME}"  ; 创建开始菜单快捷方式
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${MAIN_PROGRAM_NAME}"  ; 创建桌面快捷方式
  File "${PRODUCT_LOCATION}\${MAIN_PROGRAM_NAME}"
SectionEnd

; 创建开始菜单程序卸载快捷方式
Section -AdditionalIcons
  WriteUninstaller "$INSTDIR\uninst.exe"  ; 写入卸载程序
SectionEnd

; 写注册表
Section -Post
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${MAIN_PROGRAM_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${MAIN_PROGRAM_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
SectionEnd

Section "RUNASADMIN"
 	;针对当前用户有效
	WriteRegStr HKCU "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$INSTDIR\${MAIN_PROGRAM_NAME}" "RUNASADMIN"
	;针对所有用户有效
	WriteRegStr HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" "$INSTDIR\${MAIN_PROGRAM_NAME}" "RUNASADMIN"
SectionEnd

/******************************
 *  以下是安装程序的卸载部分  *
 ******************************/

Section Uninstall
  ; 删除快捷方式
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"

  ; 删除开始菜单程序文件夹
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

  ; 删除整个程序文件夹
  RMDir /r "$INSTDIR"

  ; 删除注册表信息
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  SetAutoClose true  ; 自动关闭窗口
SectionEnd

#-- 根据 NSIS 脚本编辑规则，所有 Function 区段必须放置在 Section 区段之后编写，以避免安装程序出现未可预知的问题。--#

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "您确实要完全移除 $(^Name) ，及其所有的组件？" IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) 已成功地从您的计算机移除。"
FunctionEnd
