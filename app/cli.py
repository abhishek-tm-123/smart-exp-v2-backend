"""Interactive command-line client for the SmartExp API."""

import argparse
import getpass
import sys
from datetime import date

import httpx


class SmartExpCLI:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def request(self, method: str, path: str, **kwargs):
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=self.headers,
                timeout=httpx.Timeout(120.0, connect=10.0),
                **kwargs,
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", exc.response.text) if exc.response.content else exc.response.reason_phrase
            print(f"Error ({exc.response.status_code}): {detail}")
        except httpx.RequestError as exc:
            print(f"Cannot connect to the API: {exc}")
        return None

    def signup(self) -> None:
        name = input("Name: ").strip()
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        user = self.request("POST", "/auth/signup", json={"name": name, "email": email, "password": password})
        if user:
            print(f"Account created for {user['name']}. Use /login to sign in.")

    def login(self) -> None:
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        result = self.request("POST", "/auth/login", json={"email": email, "password": password})
        if result:
            self.token = result["access_token"]
            print("Signed in. Type a finance request or /help.")

    def chat(self, message: str) -> None:
        if not self.require_login():
            return
        print("Jarvis is thinking...")
        result = self.request("POST", "/chat/", json={"message": message})
        if result:
            print(f"Jarvis: {result['reply']}")
            if result.get("actions"):
                print(f"Actions: {', '.join(result['actions'])}")

    def transactions(self) -> None:
        if not self.require_login():
            return
        rows = self.request("GET", "/transactions/")
        if rows is not None:
            if not rows:
                print("No transactions yet.")
                return
            for item in rows:
                merchant = f" — {item['merchant']}" if item.get("merchant") else ""
                print(f"#{item['id']}  {item['transaction_date']}  {item['transaction_type']}  {item['amount']}  {item['category']}{merchant}")

    def summary(self, arguments: list[str]) -> None:
        if not self.require_login():
            return
        if len(arguments) != 2:
            print("Usage: /summary YYYY-MM-DD YYYY-MM-DD")
            return
        result = self.request("GET", "/transactions/summary", params={"from_date": arguments[0], "to_date": arguments[1]})
        if result:
            print(f"Period: {result['from_date']} to {result['to_date']}")
            print(f"Expenses: {result['total_expenses']} | Income: {result['total_income']} | Net: {result['net']}")
            for category in result["by_category"]:
                print(f"  {category['category']}: {category['total']}")

    def budgets(self) -> None:
        if not self.require_login():
            return
        rows = self.request("GET", "/budgets/status")
        if rows is not None:
            if not rows:
                print("No active budgets today.")
                return
            for item in rows:
                print(f"{item['category']}: spent {item['spent']} of {item['amount']} ({item['percentage_used']}%), remaining {item['remaining']}")

    def profile(self) -> None:
        if not self.require_login():
            return
        user = self.request("GET", "/auth/me")
        if user:
            print(f"{user['name']} <{user['email']}>")

    def require_login(self) -> bool:
        if not self.token:
            print("Please use /login first.")
            return False
        return True

    def run(self) -> None:
        print("SmartExp Jarvis CLI")
        print("Type /help for commands. Log in, then type a normal finance request.")
        while True:
            try:
                raw = input("smartexp> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return
            if not raw:
                continue
            command, *arguments = raw.split()
            if command in {"/quit", "/exit"}:
                print("Goodbye.")
                return
            if command == "/help":
                print("/signup, /login, /logout, /me, /transactions, /summary YYYY-MM-DD YYYY-MM-DD, /budgets, /quit")
                print("Any other text is sent to Jarvis, for example: I spent 120 on groceries today.")
            elif command == "/signup":
                self.signup()
            elif command == "/login":
                self.login()
            elif command == "/logout":
                self.token = None
                print("Signed out.")
            elif command == "/me":
                self.profile()
            elif command == "/transactions":
                self.transactions()
            elif command == "/summary":
                self.summary(arguments)
            elif command == "/budgets":
                self.budgets()
            elif command.startswith("/"):
                print("Unknown command. Type /help.")
            else:
                self.chat(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartExp interactive CLI")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="SmartExp API URL")
    args = parser.parse_args()
    SmartExpCLI(args.api_url).run()


if __name__ == "__main__":
    main()
