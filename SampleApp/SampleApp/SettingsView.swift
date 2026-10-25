import SwiftUI

struct SettingsView: View {
    @State private var isNotificationEnabled = true
    @State private var isDarkModeEnabled = false

    var body: some View {
        Form {
            Toggle("通知", isOn: $isNotificationEnabled)
            Toggle("ダークモード", isOn: $isDarkModeEnabled)
        }
        .navigationTitle("設定")
    }
}

#Preview {
    NavigationStack {
        SettingsView()
    }
}
