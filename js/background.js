chrome.browserAction.onClicked.addListener(function (tab) {
	// when the browserAction icon is clicked, create a new window
	var windowParams = {"url": "http://localhost:8777/init", "width": 100, "height": 300, "type": "popup"};
	chrome.windows.create(windowParams, function (window) {
		//chrome.windows.update(window.id, {"width": 100});
		console.info('got a window');
		console.info(window);
	});
});
