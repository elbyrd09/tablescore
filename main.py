from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal, Optional
import random
import uuid

from db import (
    expire_old_rooms,
    fetch_room,
    fetch_room_by_password,
    get_session,
    init_db,
    insert_room,
    password_taken,
    room_transaction,
    used_passwords,
)
from sqlalchemy.exc import IntegrityError

app = FastAPI(title="Board Game Live Scorer - Prototype")


@app.on_event("startup")
def on_startup():
    init_db()
    session = get_session()
    try:
        expire_old_rooms(session)
        session.commit()
    finally:
        session.close()


@app.get("/")
def index(request: Request):
    html_path = Path(__file__).parent / "index.html"
    html = html_path.read_text(encoding="utf-8")
    origin = str(request.base_url).rstrip("/")
    return HTMLResponse(html.replace("__SITE_ORIGIN__", origin))


@app.get("/ads.txt")
def ads_txt():
    # Required for AdSense seller verification.
    body = "google.com, pub-7115873505287711, DIRECT, f08c47fec0942fa0\n"
    return Response(body, media_type="text/plain")


@app.get("/robots.txt")
def robots(request: Request):
    origin = str(request.base_url).rstrip("/")
    body = f"User-agent: *\nAllow: /\nSitemap: {origin}/sitemap.xml\n"
    return Response(body, media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap(request: Request):
    origin = str(request.base_url).rstrip("/")
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{origin}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n"
        "</urlset>\n"
    )
    return Response(body, media_type="application/xml")

# Easy, clean 4-letter English words for room passwords (no profanity).
ROOM_WORDS = [
    "ABLE", "ACID", "AGED", "AIDE", "ALOE", "AMMO", "APEX", "ARCH", "AREA", "ARMY",
    "AUNT", "AVID", "AWAY", "AXIS", "BAKE", "BALM", "BAND", "BANK", "BARE", "BARN",
    "BASE", "BEAD", "BEAK", "BEAM", "BEAN", "BEAR", "BEAT", "BELL", "BELT", "BEND",
    "BEST", "BIKE", "BILL", "BIND", "BIRD", "BITE", "BLUE", "BLUR", "BOAT", "BODY",
    "BOIL", "BOLD", "BOLT", "BOND", "BONE", "BOOK", "BOOM", "BOOT", "BORN", "BOWL",
    "BREW", "BRIM", "BROW", "BULB", "BULK", "BUMP", "BURN", "BUSH", "BUSY", "CAKE",
    "CALF", "CALL", "CALM", "CAMP", "CANE", "CAPE", "CARD", "CARE", "CART", "CASE",
    "CASH", "CAST", "CAVE", "CELL", "CENT", "CHAT", "CHEF", "CHEW", "CHIN", "CHIP",
    "CHOP", "CITY", "CLAM", "CLAP", "CLAW", "CLAY", "CLIP", "CLUB", "CLUE", "COAL",
    "COAT", "CODE", "COIL", "COIN", "COLD", "COLT", "COMB", "CONE", "COOK", "COOL",
    "COPE", "CORD", "CORE", "CORK", "CORN", "COST", "COZY", "CRAB", "CREW", "CROP",
    "CROW", "CUBE", "CURB", "CURE", "CURL", "CUTE", "DAMP", "DARE", "DARK", "DART",
    "DASH", "DATA", "DATE", "DAWN", "DEAL", "DEAR", "DECK", "DEED", "DEEP", "DEER",
    "DESK", "DIAL", "DICE", "DIET", "DIME", "DINE", "DIRT", "DISH", "DOCK", "DOLL",
    "DOME", "DONE", "DOOR", "DOVE", "DOWN", "DRAW", "DRIP", "DROP", "DRUM", "DUCK",
    "DUEL", "DUET", "DUKE", "DUNE", "DUSK", "DUST", "DUTY", "EACH", "EARL", "EARN",
    "EASE", "EAST", "EASY", "ECHO", "EDGE", "EDIT", "EVEN", "EVER", "EXAM", "EXIT",
    "FACE", "FACT", "FADE", "FAIL", "FAIR", "FAKE", "FALL", "FAME", "FARE", "FARM",
    "FAST", "FATE", "FAWN", "FEAR", "FEAT", "FEED", "FEEL", "FEET", "FELL", "FELT",
    "FERN", "FILE", "FILL", "FILM", "FIND", "FINE", "FIRE", "FIRM", "FISH", "FIST",
    "FIVE", "FLAG", "FLAP", "FLAT", "FLAW", "FLEW", "FLEX", "FLIP", "FLOW", "FOAM",
    "FOLD", "FOLK", "FOND", "FONT", "FOOD", "FOOT", "FORD", "FORK", "FORM", "FORT",
    "FOUR", "FREE", "FROG", "FUEL", "FULL", "FUND", "FURY", "FUSE", "GAIN", "GAME",
    "GATE", "GAZE", "GEAR", "GEMS", "GIFT", "GIRL", "GIVE", "GLAD", "GLOW", "GLUE",
    "GOAL", "GOAT", "GOLD", "GOLF", "GONE", "GOOD", "GOWN", "GRAB", "GRAM", "GRAY",
    "GREY", "GRID", "GRIN", "GRIP", "GROW", "GULF", "GUST", "HAIL", "HAIR", "HALF",
    "HALL", "HALO", "HALT", "HAND", "HANG", "HARD", "HARE", "HARM", "HARP", "HAWK",
    "HAZE", "HEAD", "HEAL", "HEAP", "HEAR", "HEAT", "HEEL", "HELD", "HERB", "HERD",
    "HERE", "HERO", "HIDE", "HIGH", "HIKE", "HILL", "HINT", "HIRE", "HOLD", "HOLE",
    "HOME", "HOOD", "HOOK", "HOPE", "HORN", "HOSE", "HOST", "HOUR", "HOWL", "HUGE",
    "HUNG", "HUNT", "HURT", "HUSH", "HYMN", "ICON", "IDEA", "IDLE", "IDOL", "INCH",
    "INFO", "INTO", "IRIS", "IRON", "ITEM", "JADE", "JAIL", "JARS", "JEAN", "JEEP",
    "JOIN", "JOKE", "JOLT", "JULY", "JUMP", "JUNE", "JURY", "JUST", "KEEN", "KEEP",
    "KELP", "KEPT", "KICK", "KIND", "KING", "KITE", "KNEE", "KNEW", "KNIT", "KNOT",
    "KNOW", "LACE", "LACK", "LADY", "LAID", "LAKE", "LAMB", "LAMP", "LAND", "LANE",
    "LARK", "LAST", "LATE", "LAVA", "LAWN", "LAZY", "LEAD", "LEAF", "LEAK", "LEAN",
    "LEAP", "LEFT", "LEND", "LENS", "LESS", "LIFT", "LIKE", "LILY", "LIME", "LINE",
    "LINK", "LION", "LIST", "LIVE", "LOAD", "LOAF", "LOAN", "LOCK", "LOFT", "LONE",
    "LONG", "LOOK", "LOOP", "LORD", "LOSE", "LOSS", "LOST", "LOUD", "LOVE", "LUCK",
    "LUNG", "LURE", "LUSH", "LYNX", "MADE", "MAID", "MAIL", "MAIN", "MAKE", "MALE",
    "MALL", "MALT", "MANY", "MARE", "MARK", "MARS", "MASK", "MASS", "MAST", "MATE",
    "MATH", "MAZE", "MEAL", "MEAN", "MEAT", "MEET", "MELT", "MEMO", "MEND", "MENU",
    "MESH", "MILD", "MILE", "MILK", "MILL", "MIND", "MINE", "MINT", "MISS", "MIST",
    "MOAT", "MODE", "MOLD", "MOLE", "MOOD", "MOON", "MORE", "MOSS", "MOST", "MOTH",
    "MOVE", "MUCH", "MULE", "MUSE", "MUST", "MUTE", "NAIL", "NAME", "NAVY", "NEAR",
    "NEAT", "NECK", "NEED", "NEST", "NEWS", "NEWT", "NEXT", "NICE", "NINE", "NODE",
    "NONE", "NOON", "NORM", "NOSE", "NOTE", "NOUN", "OAKS", "OARS", "OATH", "OATS",
    "OBEY", "OKAY", "OMEN", "ONCE", "ONLY", "ONTO", "OPEN", "ORAL", "OVAL", "OVEN",
    "OVER", "PACE", "PACK", "PAGE", "PAID", "PAIL", "PAIN", "PAIR", "PALE", "PALM",
    "PARK", "PART", "PASS", "PAST", "PATH", "PAVE", "PAWN", "PEAK", "PEAR", "PEAT",
    "PEEL", "PEER", "PEST", "PICK", "PIER", "PILE", "PILL", "PINE", "PINK", "PINT",
    "PIPE", "PLAN", "PLAY", "PLOT", "PLUM", "PLUS", "POEM", "POET", "POLE", "POLL",
    "POND", "PONY", "POOL", "POOR", "POPE", "PORE", "PORT", "POSE", "POST", "POUR",
    "PRAY", "PREY", "PROP", "PULL", "PULP", "PUMP", "PURE", "PUSH", "QUIT", "RACE",
    "RACK", "RAFT", "RAGE", "RAID", "RAIL", "RAIN", "RAKE", "RANK", "RARE", "RATE",
    "READ", "REAL", "REAP", "REED", "REEF", "RENT", "REST", "RICE", "RICH", "RIDE",
    "RING", "RIOT", "RISE", "RISK", "ROAD", "ROAM", "ROAR", "ROBE", "ROCK", "RODE",
    "ROLE", "ROLL", "ROOF", "ROOM", "ROOT", "ROPE", "ROSE", "RUBY", "RUIN", "RULE",
    "RUNG", "RUSH", "RUST", "SAFE", "SAGE", "SAID", "SAIL", "SAKE", "SALE", "SALT",
    "SAME", "SAND", "SANE", "SAVE", "SEAL", "SEAM", "SEAT", "SEED", "SEEK", "SEEM",
    "SEEN", "SELF", "SELL", "SEND", "SHIP", "SHOP", "SHOT", "SHOW", "SHUT", "SIDE",
    "SIFT", "SIGN", "SILK", "SILO", "SING", "SINK", "SITE", "SIZE", "SKIN", "SKIP",
    "SLAM", "SLED", "SLID", "SLIM", "SLIP", "SLOT", "SLOW", "SNAP", "SNOW", "SOAP",
    "SOAR", "SODA", "SOFA", "SOFT", "SOIL", "SOLD", "SOLE", "SOLO", "SOME", "SONG",
    "SOON", "SORE", "SORT", "SOUL", "SOUP", "SOUR", "SPIN", "SPIT", "SPOT", "STAR",
    "STAY", "STEM", "STEP", "STEW", "STIR", "STOP", "SUCH", "SUIT", "SULK", "SUMS",
    "SURE", "SURF", "SWAN", "SWIM", "TACK", "TACO", "TAIL", "TAKE", "TALE", "TALK",
    "TALL", "TAME", "TANK", "TAPE", "TASK", "TEAL", "TEAM", "TEAR", "TELL", "TEND",
    "TENT", "TERM", "TEST", "TEXT", "THAN", "THAT", "THEM", "THEN", "THEY", "THIN",
    "THIS", "TIDY", "TILE", "TIME", "TINY", "TIRE", "TOAD", "TOIL", "TOLD", "TOLL",
    "TOMB", "TONE", "TOOK", "TOOL", "TOPS", "TORE", "TORN",
    "TOUR", "TOWN", "TRAP", "TRAY", "TREE", "TRIM", "TRIP", "TROT", "TRUE", "TUBE",
    "TUNE", "TURN", "TWIG", "TWIN", "TYPE", "UNDO", "UNIT", "UNTO", "UPON", "URGE",
    "USED", "USER", "VASE", "VAST", "VEIL", "VEIN", "VENT", "VERB", "VERY", "VEST",
    "VETO", "VICE", "VIEW", "VINE", "VISA", "VOID", "VOLT", "VOTE", "WAGE", "WAIT",
    "WAKE", "WALK", "WALL", "WAND", "WANT", "WARD", "WARM", "WARN", "WARP", "WASH",
    "WAVE", "WAXY", "WEAK", "WEAR", "WEED", "WEEK", "WELL", "WENT", "WERE", "WEST",
    "WHAT", "WHEN", "WHIP", "WIDE", "WIFE", "WILD", "WILL", "WILT", "WIND", "WINE",
    "WING", "WIPE", "WIRE", "WISE", "WISH", "WITH", "WOLF", "WOOD", "WOOL", "WORD",
    "WORE", "WORK", "WORM", "WORN", "WRAP", "YARD", "YARN", "YEAR", "YELL", "YOGA",
    "YOUR", "ZEAL", "ZERO", "ZEST", "ZONE", "ZOOM",
]
ROOM_WORDS = sorted({w for w in ROOM_WORDS if len(w) == 4 and w.isalpha()})


class CustomGameConfig(BaseModel):
    game_description: Optional[str] = Field(default=None, max_length=500)
    optional_notes: Optional[str] = Field(default=None, max_length=300)
    how_to_win: Literal["high_score", "low_score"] = "high_score"
    how_to_end: Literal["manually", "target_score"] = "manually"
    how_to_keep_score: Literal["in_rounds", "incrementally"] = "incrementally"
    how_to_sort_players: Literal["manually", "by_score"] = "by_score"
    how_to_display_scores: Literal["total_scores", "history"] = "total_scores"
    # Optional numeric helpers when end condition needs them
    rounds_count: Optional[int] = Field(default=None, ge=1, le=999)
    target_score: Optional[int] = Field(default=None, le=999999)
    # When ending by target score: finish the round or the whole game.
    target_score_action: Optional[Literal["complete_round", "end_game"]] = None
    # Optional when how_to_win is low_score (e.g. start at 501).
    starting_score: Optional[int] = Field(default=None, le=999999)


class CreateGameRequest(BaseModel):
    game_type: Literal["preset", "custom"] = "custom"
    game_name: str
    player_names: list[str]
    password: str


class ScoreUpdateRequest(BaseModel):
    player_name: str
    metric_name: str
    value: int


class AddPlayerRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=24)


class StartingScoreRequest(BaseModel):
    starting_score: int = Field(le=999999)


class ReorderPlayersRequest(BaseModel):
    player_order: list[str]


class GameScoringEngine:
    @staticmethod
    def default_metrics(game_name: str, game_type: str) -> dict:
        return {"points": 0}

    @staticmethod
    def calculate_totals(game_name: str, raw_scores: dict, game_type: str = "custom") -> int:
        return sum(raw_scores.values())


def _normalize_password(password: str) -> str:
    return password.strip().upper()


def _allocate_password(session, preferred: Optional[str] = None) -> str:
    """Pick an unused 4-letter room password (after optional TTL cleanup)."""
    expire_old_rooms(session)

    if preferred:
        candidate = _normalize_password(preferred)
        if len(candidate) != 4 or not candidate.isalpha():
            raise HTTPException(status_code=400, detail="Password must be a 4-letter word.")
        if candidate not in ROOM_WORDS:
            raise HTTPException(status_code=400, detail="Password is not an allowed room word.")
        if password_taken(session, candidate):
            raise HTTPException(
                status_code=409,
                detail="That room password is already in use. Refresh for a new one.",
            )
        return candidate

    taken = used_passwords(session)
    available = [w for w in ROOM_WORDS if w not in taken]
    if not available:
        raise HTTPException(status_code=503, detail="No room passwords available. Try again later.")
    return random.choice(available)


def _require_room(room_token: str) -> dict:
    """Read-only load (no row lock). Prefer room_transaction for writes."""
    session = get_session()
    try:
        room = fetch_room(session, room_token)
    finally:
        session.close()
    if not room:
        raise HTTPException(status_code=404, detail="Game session not found.")
    return room


def _ensure_play_fields(room: dict) -> None:
    """Backfill play-state fields for older in-memory rooms."""
    players = room.get("players", {})
    if "player_order" not in room:
        room["player_order"] = list(players.keys())
    if "status" not in room:
        room["status"] = "active"
    if "current_round" not in room:
        room["current_round"] = 1
    if "round_history" not in room:
        room["round_history"] = []
    if "winner" not in room:
        room["winner"] = None
    if "ended_reason" not in room:
        room["ended_reason"] = None
    if "winner_note" not in room:
        room["winner_note"] = None
    for name, player in players.items():
        player.setdefault("cumulative_score", player.get("live_total_score", 0))
        player.setdefault("round_wins", 0)


def _config(room: dict) -> dict:
    return room.get("custom_config") or {}


def _total_rounds(room: dict) -> Optional[int]:
    config = _config(room)
    if (
        config.get("how_to_end") == "target_score"
        and config.get("target_score_action") == "complete_round"
    ):
        return config.get("rounds_count") or 1
    if config.get("how_to_keep_score") == "incrementally":
        return 1
    return None


def _initial_points(config: dict) -> int:
    if config.get("how_to_win") == "low_score":
        score = config.get("starting_score")
        return int(score) if score is not None else 0
    return 0


def _fresh_player(config: dict) -> dict:
    points = _initial_points(config)
    return {
        "raw_metrics": {"points": points},
        "live_total_score": points,
        "cumulative_score": 0 if config.get("how_to_keep_score") == "in_rounds" else points,
        "round_wins": 0,
    }


def _score_for_comparison(player: dict, config: dict) -> int:
    """Prefer cumulative for round-based games; live total for incremental."""
    if config.get("how_to_keep_score") == "in_rounds":
        return int(player.get("cumulative_score", 0))
    return int(player.get("live_total_score", 0))


def _target_hit(score: int, target: int, how_to_win: str) -> bool:
    if how_to_win == "low_score":
        return score <= target
    return score >= target


def _pick_winners_by_score(named_scores: dict[str, int], how_to_win: str) -> list[str]:
    if not named_scores:
        return []
    if how_to_win == "low_score":
        best = min(named_scores.values())
    else:
        best = max(named_scores.values())
    return [name for name, score in named_scores.items() if score == best]


def _end_game(room: dict, reason: str) -> None:
    if room.get("status") == "ended":
        return

    config = _config(room)
    how_to_win = config.get("how_to_win", "high_score")
    keep = config.get("how_to_keep_score", "incrementally")
    winner_note = None

    # Round-based matches are decided by round-win balance once rounds exist.
    if keep == "in_rounds" and any(p.get("round_wins", 0) > 0 for p in room["players"].values()):
        named_wins = {name: int(data.get("round_wins", 0)) for name, data in room["players"].items()}
        top_wins = max(named_wins.values())
        tied = [name for name, wins in named_wins.items() if wins == top_wins]

        if len(tied) == 1:
            winners = tied
            win_label = "win" if top_wins == 1 else "wins"
            winner_note = f"{tied[0]} wins with {top_wins} round {win_label}!"
        else:
            # Tied round wins (common with an even round count): break by score.
            score_map = {
                name: int(room["players"][name].get("cumulative_score", 0))
                for name in tied
            }
            score_winners = _pick_winners_by_score(score_map, how_to_win)
            win_label = "win" if top_wins == 1 else "wins"
            if len(score_winners) == 1:
                winners = score_winners
                score = score_map[score_winners[0]]
                adjective = "lowest" if how_to_win == "low_score" else "highest"
                winner_note = (
                    f"{score_winners[0]} wins because they have the {adjective} score "
                    f"({score}) with {top_wins} round {win_label}"
                )
            else:
                winners = score_winners
                winner_note = (
                    f"Tie: {' & '.join(winners)} — {top_wins} round {win_label} "
                    f"and matching scores"
                )
    else:
        # Live scores so mid-round target ends (start 10 → target 0) rank correctly.
        named = {
            name: int(data.get("live_total_score", 0))
            for name, data in room["players"].items()
        }
        winners = _pick_winners_by_score(named, how_to_win)
        if len(winners) == 1:
            winner_note = f"{winners[0]} wins!"
        elif winners:
            winner_note = f"Tie: {' & '.join(winners)}"

    room["status"] = "ended"
    room["ended_reason"] = reason
    room["winner"] = winners[0] if len(winners) == 1 else None
    room["winners"] = winners
    room["winner_note"] = winner_note


def _apply_complete_round(room: dict) -> None:
    """Archive the current round, award round wins, and advance or end."""
    config = _config(room)
    how_to_win = config.get("how_to_win", "high_score")
    round_scores = {
        name: int(data.get("live_total_score", 0))
        for name, data in room["players"].items()
    }
    winners = _pick_winners_by_score(round_scores, how_to_win)
    reset_points = _initial_points(config)

    for name, data in room["players"].items():
        data["cumulative_score"] = int(data.get("cumulative_score", 0)) + int(data.get("live_total_score", 0))
        if name in winners:
            data["round_wins"] = int(data.get("round_wins", 0)) + 1
        data["raw_metrics"] = {"points": reset_points}
        data["live_total_score"] = reset_points

    room["round_history"].append({
        "round": room["current_round"],
        "scores": round_scores,
        "winners": winners,
    })

    total = _total_rounds(room)
    finished_round = room["current_round"]
    if total and finished_round >= total:
        _end_game(room, "rounds")
    else:
        room["current_round"] = finished_round + 1


def _check_target_end(room: dict) -> None:
    config = _config(room)
    if room.get("status") != "active":
        return
    if config.get("how_to_end") != "target_score":
        return

    target = config.get("target_score")
    if target is None:
        return

    how_to_win = config.get("how_to_win", "high_score")
    action = config.get("target_score_action") or "end_game"

    # Always use the live/active score. In-rounds cumulative stays 0 until a
    # round is completed, which falsely ended Low Score games with target 0.
    scores = {
        name: int(data.get("live_total_score", 0))
        for name, data in room["players"].items()
    }

    if not any(_target_hit(score, target, how_to_win) for score in scores.values()):
        return

    if action == "complete_round":
        _apply_complete_round(room)
    else:
        _end_game(room, "target_score")


def _public_state(room: dict) -> dict:
    _ensure_play_fields(room)
    return {
        "room_token": room["room_token"],
        "password": room["password"],
        "game_type": room["game_type"],
        "game_name": room["game_name"],
        "setup_complete": room["setup_complete"],
        "custom_config": room.get("custom_config"),
        "players": room["players"],
        "player_order": room.get("player_order", list(room["players"].keys())),
        "status": room.get("status", "active"),
        "current_round": room.get("current_round", 1),
        "total_rounds": _total_rounds(room),
        "round_history": room.get("round_history", []),
        "winner": room.get("winner"),
        "winners": room.get("winners"),
        "winner_note": room.get("winner_note"),
        "ended_reason": room.get("ended_reason"),
    }


@app.get("/room/password")
def suggest_password():
    """Return a fresh unused 4-letter room password for the create form."""
    session = get_session()
    try:
        password = _allocate_password(session)
        session.commit()
        return {"password": password}
    finally:
        session.close()


@app.post("/game/start")
def start_game(request: CreateGameRequest):
    if not request.player_names:
        raise HTTPException(status_code=400, detail="At least one player is required.")

    game_name = request.game_name.strip()
    if not game_name:
        raise HTTPException(status_code=400, detail="Game name is required.")

    if request.game_type == "preset":
        raise HTTPException(status_code=400, detail="Preset games are not available. Create a custom game.")

    session = get_session()
    try:
        password = _allocate_password(session, request.password)
        room_token = uuid.uuid4().hex

        metrics_template = GameScoringEngine.default_metrics(game_name, request.game_type)
        initial_players = {}
        player_order = []
        for name in request.player_names:
            cleaned = name.strip()
            if not cleaned:
                continue
            if cleaned in initial_players:
                continue
            player_order.append(cleaned)
            initial_players[cleaned] = {
                "raw_metrics": dict(metrics_template),
                "live_total_score": 0,
                "cumulative_score": 0,
                "round_wins": 0,
            }

        if not initial_players:
            raise HTTPException(status_code=400, detail="At least one player is required.")

        room = {
            "room_token": room_token,
            "password": password,
            "game_type": request.game_type,
            "game_name": game_name,
            "setup_complete": request.game_type != "custom",
            "custom_config": None,
            "players": initial_players,
            "player_order": player_order,
            "status": "active",
            "current_round": 1,
            "round_history": [],
            "winner": None,
            "winners": None,
            "winner_note": None,
            "ended_reason": None,
        }

        insert_room(session, room)
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="That room password is already in use. Refresh for a new one.",
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {
        "room_token": room_token,
        "password": password,
        "message": "Game session successfully created!",
        "state": _public_state(room),
    }


@app.get("/game/join/{password}")
def join_by_password(password: str):
    """Grant access to a room via its shareable 4-letter password."""
    key = _normalize_password(password)
    session = get_session()
    try:
        room = fetch_room_by_password(session, key)
    finally:
        session.close()
    if not room:
        raise HTTPException(status_code=404, detail="No room found for that password.")
    return _public_state(room)


@app.get("/game/{room_token}")
def get_game_state(room_token: str):
    return _public_state(_require_room(room_token))


@app.post("/game/{room_token}/setup")
def complete_custom_setup(room_token: str, config: CustomGameConfig):
    try:
        with room_transaction(room_token) as room:
            if room["game_type"] != "custom":
                raise HTTPException(status_code=400, detail="Only custom games use this setup flow.")

            if config.how_to_end == "target_score" and config.target_score is None:
                raise HTTPException(status_code=400, detail="Target score is required when ending by target score.")
            if config.how_to_end == "target_score" and not config.target_score_action:
                raise HTTPException(
                    status_code=400,
                    detail="Choose whether the target score completes a round or ends the game.",
                )
            if (
                config.how_to_end == "target_score"
                and config.target_score_action == "complete_round"
                and not config.rounds_count
            ):
                raise HTTPException(
                    status_code=400,
                    detail="# of rounds completed is required when target score completes a round.",
                )

            if config.optional_notes and len(config.optional_notes) > 300:
                raise HTTPException(status_code=400, detail="Optional notes must be 300 characters or fewer.")

            payload = config.model_dump()
            # Target that completes rounds implies round-based scoring.
            if payload["how_to_end"] == "target_score" and payload.get("target_score_action") == "complete_round":
                payload["how_to_keep_score"] = "in_rounds"
            if payload["how_to_end"] != "target_score":
                payload["target_score_action"] = None
                payload["rounds_count"] = None
            if payload["how_to_win"] != "low_score":
                payload["starting_score"] = None

            room["custom_config"] = payload
            room["setup_complete"] = True
            room["status"] = "active"
            room["current_round"] = 1
            room["round_history"] = []
            room["winner"] = None
            room["winners"] = None
            room["winner_note"] = None
            room["ended_reason"] = None
            room["player_order"] = list(room["players"].keys())
            for name in room["players"]:
                room["players"][name] = _fresh_player(payload)

            return {"message": "Custom game setup saved.", "state": _public_state(room)}
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")


@app.post("/game/{room_token}/update")
def update_score(room_token: str, request: ScoreUpdateRequest):
    try:
        with room_transaction(room_token) as room:
            _ensure_play_fields(room)

            if not room["setup_complete"]:
                raise HTTPException(status_code=400, detail="Finish game setup before scoring.")
            if room.get("status") == "ended":
                raise HTTPException(status_code=400, detail="This game has ended.")

            if request.player_name not in room["players"]:
                raise HTTPException(status_code=404, detail="Player not found in this session.")

            player_data = room["players"][request.player_name]

            if request.metric_name not in player_data["raw_metrics"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric '{request.metric_name}' for this game.",
                )

            player_data["raw_metrics"][request.metric_name] = request.value
            player_data["live_total_score"] = GameScoringEngine.calculate_totals(
                room["game_name"],
                player_data["raw_metrics"],
                room["game_type"],
            )

            # Incremental scores are the running total; round mode keeps a separate cumulative.
            if _config(room).get("how_to_keep_score") == "incrementally":
                player_data["cumulative_score"] = player_data["live_total_score"]

            _check_target_end(room)

            return {
                "message": "Score updated live!",
                "updated_player": player_data,
                "state": _public_state(room),
            }
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")


@app.post("/game/{room_token}/players")
def add_player(room_token: str, request: AddPlayerRequest):
    try:
        with room_transaction(room_token) as room:
            _ensure_play_fields(room)

            if not room["setup_complete"]:
                raise HTTPException(status_code=400, detail="Finish game setup before adding players.")
            if room.get("status") == "ended":
                raise HTTPException(status_code=400, detail="This game has ended.")

            name = request.player_name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="Player name is required.")
            if name in room["players"]:
                raise HTTPException(status_code=409, detail="That player is already in this room.")

            room["players"][name] = _fresh_player(_config(room))
            room["player_order"].append(name)

            return {"message": f"{name} joined the table.", "state": _public_state(room)}
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")


@app.post("/game/{room_token}/starting-score")
def set_starting_score(room_token: str, request: StartingScoreRequest):
    try:
        with room_transaction(room_token) as room:
            _ensure_play_fields(room)

            if not room["setup_complete"]:
                raise HTTPException(status_code=400, detail="Finish game setup first.")
            if room.get("status") == "ended":
                raise HTTPException(status_code=400, detail="This game has ended.")

            config = _config(room)
            if config.get("how_to_win") != "low_score":
                raise HTTPException(status_code=400, detail="Starting score is only used for Low Score games.")

            config["starting_score"] = request.starting_score
            room["custom_config"] = config

            points = request.starting_score
            for player in room["players"].values():
                player["raw_metrics"] = {"points": points}
                player["live_total_score"] = points
                if config.get("how_to_keep_score") == "incrementally":
                    player["cumulative_score"] = points

            return {"message": "Starting score applied.", "state": _public_state(room)}
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")


@app.post("/game/{room_token}/play-again")
def play_again(room_token: str):
    """Reset scores and rounds for another match with the same players and rules."""
    try:
        with room_transaction(room_token) as room:
            _ensure_play_fields(room)

            if not room["setup_complete"]:
                raise HTTPException(status_code=400, detail="Finish game setup before playing again.")

            config = _config(room)
            if not config:
                raise HTTPException(status_code=400, detail="Game rules are missing.")

            room["status"] = "active"
            room["current_round"] = 1
            room["round_history"] = []
            room["winner"] = None
            room["winners"] = None
            room["winner_note"] = None
            room["ended_reason"] = None
            for name in list(room["players"].keys()):
                room["players"][name] = _fresh_player(config)

            return {"message": "New game started.", "state": _public_state(room)}
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")


@app.post("/game/{room_token}/complete-round")
def complete_round(room_token: str):
    try:
        with room_transaction(room_token) as room:
            _ensure_play_fields(room)

            if not room["setup_complete"]:
                raise HTTPException(status_code=400, detail="Finish game setup before scoring.")
            if room.get("status") == "ended":
                raise HTTPException(status_code=400, detail="This game has ended.")

            config = _config(room)
            if config.get("how_to_keep_score") != "in_rounds":
                raise HTTPException(
                    status_code=400,
                    detail="Complete round is only used for round-based scoring.",
                )

            finished_round = room["current_round"]
            _apply_complete_round(room)

            return {"message": f"Round {finished_round} complete.", "state": _public_state(room)}
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")


@app.post("/game/{room_token}/end")
def end_game(room_token: str):
    try:
        with room_transaction(room_token) as room:
            _ensure_play_fields(room)

            if not room["setup_complete"]:
                raise HTTPException(status_code=400, detail="Finish game setup before ending.")
            if room.get("status") == "ended":
                return {"message": "Game already ended.", "state": _public_state(room)}

            # If currently mid-round with round scoring, fold the open round into the record first.
            config = _config(room)
            if config.get("how_to_keep_score") == "in_rounds":
                start = _initial_points(config)
                if any(int(p.get("live_total_score", 0)) != start for p in room["players"].values()):
                    how_to_win = config.get("how_to_win", "high_score")
                    round_scores = {
                        name: int(data.get("live_total_score", 0))
                        for name, data in room["players"].items()
                    }
                    winners = _pick_winners_by_score(round_scores, how_to_win)
                    for name, data in room["players"].items():
                        data["cumulative_score"] = int(data.get("cumulative_score", 0)) + int(
                            data.get("live_total_score", 0)
                        )
                        if name in winners:
                            data["round_wins"] = int(data.get("round_wins", 0)) + 1
                        data["raw_metrics"] = {"points": start}
                        data["live_total_score"] = start
                    room["round_history"].append({
                        "round": room["current_round"],
                        "scores": round_scores,
                        "winners": winners,
                    })

            _end_game(room, "manual")
            return {"message": "Game ended.", "state": _public_state(room)}
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")


@app.post("/game/{room_token}/reorder")
def reorder_players(room_token: str, request: ReorderPlayersRequest):
    try:
        with room_transaction(room_token) as room:
            _ensure_play_fields(room)

            if room.get("status") == "ended":
                raise HTTPException(status_code=400, detail="This game has ended.")

            config = _config(room)
            if config.get("how_to_sort_players") != "manually":
                raise HTTPException(status_code=400, detail="Manual sorting is not enabled for this room.")

            names = request.player_order
            current = set(room["players"].keys())
            if set(names) != current or len(names) != len(current):
                raise HTTPException(
                    status_code=400,
                    detail="player_order must include each player exactly once.",
                )

            room["player_order"] = names
            return {"message": "Player order updated.", "state": _public_state(room)}
    except LookupError:
        raise HTTPException(status_code=404, detail="Game session not found.")
