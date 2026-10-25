import SwiftUI

struct SettingsView: View {
    @State private var isNotificationEnabled = true
    @State private var isDarkModeEnabled = false
    @State private var isAnalyticsEnabled = true

    var body: some View {
        Form {
            Section("一般") {
                Toggle("通知", isOn: $isNotificationEnabled)
                Toggle("ダークモード", isOn: $isDarkModeEnabled)
            }
            Section("プライバシー") {
                Toggle("利用状況の送信", isOn: $isAnalyticsEnabled)
            }
        }
        .navigationTitle("設定")
    }
}

#Preview {
    NavigationStack {
        SettingsView()
    }
}
