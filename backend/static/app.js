const tokenKey = "healthguide_token";
let isLogin = false;
const $ = (id) => document.getElementById(id);

function showAuth() { $("auth-view").classList.remove("hidden"); $("chat-view").classList.add("hidden"); }
function showChat(name) { $("auth-view").classList.add("hidden"); $("chat-view").classList.remove("hidden"); $("welcome").textContent = `Welcome, ${name}. How can I help?`; loadHistory(); }
function addMessage(role, content) { const item = document.createElement("div"); item.className = `message ${role}`; item.textContent = content; $("messages").append(item); $("messages").scrollTop = $("messages").scrollHeight; }
function api(path, options = {}) { return fetch(path, { ...options, headers: { "Content-Type": "application/json", ...(localStorage.getItem(tokenKey) ? { Authorization: `Bearer ${localStorage.getItem(tokenKey)}` } : {}), ...options.headers } }); }

$("auth-toggle").onclick = () => { isLogin = !isLogin; $("name").classList.toggle("hidden", isLogin); $("auth-submit").textContent = isLogin ? "Log in" : "Create account"; $("auth-toggle").textContent = isLogin ? "Need an account? Register" : "Already have an account? Log in"; };
$("auth-form").onsubmit = async (event) => { event.preventDefault(); $("auth-error").textContent = ""; const payload = { email: $("email").value, password: $("password").value, ...(isLogin ? {} : { name: $("name").value }) }; const response = await api(`/api/auth/${isLogin ? "login" : "register"}`, { method: "POST", body: JSON.stringify(payload) }); const data = await response.json(); if (!response.ok) return $("auth-error").textContent = data.detail || "Please try again."; localStorage.setItem(tokenKey, data.access_token); localStorage.setItem("healthguide_name", data.name); showChat(data.name); };
$("logout").onclick = () => { localStorage.clear(); showAuth(); };
async function loadHistory() { $("messages").replaceChildren(); const response = await api("/api/history"); if (!response.ok) return; const data = await response.json(); if (data.length) data.forEach((message) => addMessage(message.role, message.content)); else addMessage("assistant", "Hello. I can provide general health information in English. What would you like to know?"); }
$("chat-form").onsubmit = async (event) => { event.preventDefault(); const input = $("message"), text = input.value.trim(); if (!text) return; input.value = ""; $("chat-error").textContent = ""; addMessage("user", text); const response = await api("/api/chat", { method: "POST", body: JSON.stringify({ message: text }) }); const data = await response.json(); if (!response.ok) return $("chat-error").textContent = data.detail || "Unable to send your message."; addMessage("assistant", data.reply); };
const savedToken = localStorage.getItem(tokenKey); savedToken ? showChat(localStorage.getItem("healthguide_name") || "there") : showAuth();
