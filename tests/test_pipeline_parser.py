import pytest

from services.pipeline_parser import PipelineParseError, parse
from bson import ObjectId, Regex


EXAMPLE_PIPELINE = '''
[
  {
    $match: {
      project_id: ObjectId("6a864051a4efbe696698bb61"),
      message: "retirada_registrada_no_cadastro",
      //timestamp: { $gt: "2026-08-10" }
      timestamp: {
        $regex: "^2026-08-23"
      }
    }
  },
  {
    $project: {
      _id: 0,
      horario: "$timestamp",
      email: "$data.email",
      userId: "$data.id",
      session: "$data.session_id",
      // productsPicked: "$data.products_picked",
      recall: {
        $ifNull: ["$data.recalled", false]
      }
    }
  },
  {
    $sort: {
      horario: 1
    }
  }
]
'''


def test_parses_example_pipeline_with_comments_and_objectid():
    stages = parse(EXAMPLE_PIPELINE)
    assert len(stages) == 3
    assert stages[0]["$match"]["project_id"] == ObjectId("6a864051a4efbe696698bb61")
    assert stages[0]["$match"]["message"] == "retirada_registrada_no_cadastro"
    assert stages[0]["$match"]["timestamp"] == Regex("^2026-08-23")
    assert "productsPicked" not in stages[1]["$project"]
    assert stages[2]["$sort"] == {"horario": 1}


def test_parses_isodate_range():
    text = '''[
      { $match: { timestamp: { $gte: ISODate("2026-08-23T00:00:00Z"), $lt: ISODate("2026-08-25T00:00:00Z") } } }
    ]'''
    stages = parse(text)
    clause = stages[0]["$match"]["timestamp"]
    assert clause["$gte"].strftime("%Y-%m-%d") == "2026-08-23"
    assert clause["$lt"].strftime("%Y-%m-%d") == "2026-08-25"


def test_parses_strict_json_pipeline():
    stages = parse('[{"$match": {"status": "ok"}}]')
    assert stages == [{"$match": {"status": "ok"}}]


def test_rejects_malformed_json():
    with pytest.raises(PipelineParseError):
        parse('[{ $match: { status: } }]')


def test_rejects_non_list_pipeline():
    with pytest.raises(PipelineParseError):
        parse('{ "$match": { "status": "ok" } }')


def test_rejects_out_stage():
    with pytest.raises(PipelineParseError):
        parse('[{ $match: { status: "ok" } }, { $out: "other_collection" }]')


def test_rejects_merge_stage():
    with pytest.raises(PipelineParseError):
        parse('[{ $merge: { into: "other_collection" } }]')


def test_rejects_empty_text():
    with pytest.raises(PipelineParseError):
        parse('   ')
