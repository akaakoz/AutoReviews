import SwiftUI

struct ProfileView: View {
    var body: some View {
        List {
            Section {
                HStack(spacing: 16) {
                    Image(systemName: "person.crop.circle.fill")
                        .font(.system(size: 56))
                        .foregroundStyle(.indigo)
                    VStack(alignment: .leading) {
                        Text("山田 太郎")
                            .font(.headline)
                        Text("taro@example.com")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 8)
            }
            Section("アカウント") {
                LabeledContent("プラン", value: "フリー")
                LabeledContent("登録日", value: "2026/10/01")
            }
        }
        .navigationTitle("プロフィール")
    }
}

#Preview {
    NavigationStack {
        ProfileView()
    }
}
