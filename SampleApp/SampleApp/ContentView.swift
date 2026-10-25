import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationStack {
            List {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("ようこそ")
                            .font(.title2.bold())
                        Text("今日もよい一日を")
                            .font(.subheadline)
                    }
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(.indigo.gradient, in: .rect(cornerRadius: 12))
                    .listRowInsets(EdgeInsets())
                }
                Section("お知らせ") {
                    Label("新しいバージョンが公開されました", systemImage: "sparkles")
                    Label("メンテナンスのお知らせ", systemImage: "wrench.and.screwdriver")
                }
                Section {
                    NavigationLink("プロフィール") {
                        ProfileView()
                    }
                    NavigationLink("設定") {
                        SettingsView()
                    }
                }
            }
            .navigationTitle("ホーム")
        }
        .tint(.indigo)
    }
}

#Preview {
    ContentView()
}
