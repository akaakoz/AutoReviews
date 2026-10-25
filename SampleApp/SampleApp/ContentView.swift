import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("お知らせ") {
                    Text("新しいバージョンが公開されました")
                    Text("メンテナンスのお知らせ")
                }
                Section {
                    NavigationLink("設定") {
                        SettingsView()
                    }
                }
            }
            .navigationTitle("ホーム")
        }
    }
}

#Preview {
    ContentView()
}
