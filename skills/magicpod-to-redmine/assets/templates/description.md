### 概要
* テストケース: {{test_case_link}}
* テスト実行: {{test_run_link}}
* 一括実行: {{batch_run_link}}
* ステータス: {{status}}
{{#test_setting_name}}
* テスト設定: {{test_setting_name}}
{{/test_setting_name}}
{{#pattern}}
* 実行パターン: {{pattern}}
{{/pattern}}
{{#data_pattern_number}}
* データパターン: {{data_pattern_number}}
{{/data_pattern_number}}
{{#branch}}
* ブランチ: {{branch}}
{{/branch}}
{{#started_at}}
* 実行日時: {{started_at}}
{{/started_at}}
{{#data_pattern_values}}

### データパターンの値
```
{{data_pattern_values}}
```
{{/data_pattern_values}}
{{#failed_step}}

### 失敗ステップ
```
{{failed_step}}
```
{{/failed_step}}
{{#failure_ui}}

### 失敗したUI要素
{{failure_ui}}
{{/failure_ui}}
{{#error_message}}

### エラーメッセージ
```
{{error_message}}
```
{{/error_message}}
{{#failure_analysis}}

### MagicPod 失敗分析
{{failure_analysis}}
{{/failure_analysis}}
{{#notes}}

### メモ
{{notes}}
{{/notes}}

_このチケットは magicpod-to-redmine スキルにより自動作成されました。_
