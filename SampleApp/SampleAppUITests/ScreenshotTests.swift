import XCTest

final class ScreenshotTests: XCTestCase {
    // MARK: - Lifecycle

    override func setUp() {
        continueAfterFailure = false
    }

    // MARK: - Tests

    @MainActor
    func testHome() {
        let app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.navigationBars["ホーム"].waitForExistence(timeout: 10))
        attachScreenshot(named: "Home")
    }

    @MainActor
    func testSettings() {
        let app = XCUIApplication()
        app.launch()
        app.buttons["設定"].tap()
        XCTAssertTrue(app.navigationBars["設定"].waitForExistence(timeout: 10))
        attachScreenshot(named: "Settings")
    }
}

// MARK: - Private

private extension ScreenshotTests {
    @MainActor
    func attachScreenshot(named name: String) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
