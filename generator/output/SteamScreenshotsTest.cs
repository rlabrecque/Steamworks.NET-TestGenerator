using UnityEngine;
using System.Collections;
using Steamworks;

public class SteamScreenshotsTest : MonoBehaviour {
	private ScreenshotHandle m_ScreenshotHandle;
	private bool m_Hooked;

	protected Callback<ScreenshotReady_t> m_ScreenshotReady;
	protected Callback<ScreenshotRequested_t> m_ScreenshotRequested;

	public void OnEnable() {
		
		m_ScreenshotReady = Callback<ScreenshotReady_t>.Create(OnScreenshotReady);
		m_ScreenshotRequested = Callback<ScreenshotRequested_t>.Create(OnScreenshotRequested);
	}

	public void RenderOnGUI() {
		GUILayout.BeginArea(new Rect(Screen.width - 120, 0, 120, Screen.height));
		GUILayout.Label("Variables:");
		GUILayout.Label("m_ScreenshotHandle: " + m_ScreenshotHandle);
		GUILayout.Label("m_Hooked: " + m_Hooked);
		GUILayout.EndArea();

		if (GUILayout.Button("WriteScreenshot(RGB, (uint)RGB.Length, Screen.width, Screen.height)")) {
			// We start a Coroutine with the actual implementation of this test because Texture2D.ReadPixels() has to be called at the end of the frame.
			StartCoroutine(WriteScreenshot());
			ScreenshotHandle ret = SteamScreenshots.WriteScreenshot(RGB, (uint)RGB.Length, Screen.width, Screen.height);
			print("SteamScreenshots.WriteScreenshot(" + RGB + ", " + (uint)RGB.Length + ", " + Screen.width + ", " + Screen.height + ") : " + ret);
		}

		if (GUILayout.Button("AddScreenshotToLibrary(Application.dataPath + \"/screenshot.png\", \"\", Screen.width, Screen.height)")) {
			Application.CaptureScreenshot("screenshot.png");
			// Application.CaptureScreenshot is asyncronous, therefore we have to wait until the screenshot is created.
			StartCoroutine(AddScreenshotToLibrary());
			ScreenshotHandle ret = SteamScreenshots.AddScreenshotToLibrary(Application.dataPath + "/screenshot.png", "", Screen.width, Screen.height);
			print("SteamScreenshots.AddScreenshotToLibrary(" + Application.dataPath + "/screenshot.png", "" + ", " + Screen.width + ", " + Screen.height + ") : " + ret);
		}

		if (GUILayout.Button("TriggerScreenshot()")) {
			SteamScreenshots.TriggerScreenshot();
			print("SteamScreenshots.TriggerScreenshot()");
		}

		if (GUILayout.Button("HookScreenshots(!m_Hooked)")) {
			SteamScreenshots.HookScreenshots(!m_Hooked);
			print("SteamScreenshots.HookScreenshots(" + !m_Hooked + ")");
			m_Hooked = !m_Hooked;
		}

		if (GUILayout.Button("SetLocation(m_ScreenshotHandle, \"LocationTest\")")) {
			bool ret = SteamScreenshots.SetLocation(m_ScreenshotHandle, "LocationTest");
			print("SteamScreenshots.SetLocation(" + m_ScreenshotHandle + ", " + "LocationTest" + ") : " + ret);
		}

		if (GUILayout.Button("TagUser(m_ScreenshotHandle, (CSteamID)76561197991230424)")) {
			bool ret = SteamScreenshots.TagUser(m_ScreenshotHandle, (CSteamID)76561197991230424);
			print("SteamScreenshots.TagUser(" + m_ScreenshotHandle + ", " + (CSteamID)76561197991230424 + ") : " + ret);
		}

		if (GUILayout.Button("TagPublishedFile(m_ScreenshotHandle, (PublishedFileId_t)0)")) {
			bool ret = SteamScreenshots.TagPublishedFile(m_ScreenshotHandle, (PublishedFileId_t)0);
			print("SteamScreenshots.TagPublishedFile(" + m_ScreenshotHandle + ", " + (PublishedFileId_t)0 + ") : " + ret);
		}
	}

	void OnScreenshotReady(ScreenshotReady_t pCallback) {
		Debug.Log("[" + ScreenshotReady_t.k_iCallback + " - ScreenshotReady] - " + pCallback.m_hLocal + " -- " + pCallback.m_eResult);
	}

	void OnScreenshotRequested(ScreenshotRequested_t pCallback) {
		Debug.Log("[" + ScreenshotRequested_t.k_iCallback + " - ScreenshotRequested]");
	}
}
